"""API Client for Crestron Home."""
import asyncio
import logging
import os
import ssl
import time
from typing import Any, Dict, List, Optional, cast

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CRESTRON_API_PATH,
    CRESTRON_MAX_LEVEL,
    CRESTRON_SESSION_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class CrestronApiError(Exception):
    """Exception to indicate a general API error."""


class CrestronAuthError(CrestronApiError):
    """Exception to indicate an authentication error."""


class CrestronConnectionError(CrestronApiError):
    """Exception to indicate a connection error."""


class CrestronClient:
    """API Client for Crestron Home."""

    def __init__(
        self, hass: HomeAssistant, host: str, token: str
    ) -> None:
        """Initialize the API client."""
        self.hass = hass
        self.host = host
        self.api_token = token
        self.base_url = f"https://{host}{CRESTRON_API_PATH}"
        self.auth_key: Optional[str] = None
        self.last_login: float = 0
        self.rooms: List[Dict[str, Any]] = []
        self._session = async_get_clientsession(hass, verify_ssl=False)
        self._ssl_context = None
        
        # Add a lock for login to prevent multiple simultaneous login attempts
        self._login_lock = asyncio.Lock()

    async def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context in executor to avoid blocking the event loop."""
        def _create_context():
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context
            
        return await self.hass.async_add_executor_job(_create_context)

    async def login(self) -> None:
        """Login to the Crestron Home system."""
        # Check if we need to login (session expires after 10 minutes)
        current_time = time.time()
        if self.auth_key and (current_time - self.last_login) < CRESTRON_SESSION_TIMEOUT:
            _LOGGER.debug("Session is still valid, skipping login")
            return

        # Use the lock to prevent multiple simultaneous login attempts
        async with self._login_lock:
            # Check again after acquiring the lock in case another task has already logged in
            current_time = time.time()
            if self.auth_key and (current_time - self.last_login) < CRESTRON_SESSION_TIMEOUT:
                _LOGGER.debug("Session is still valid, skipping login (after lock)")
                return
                
            _LOGGER.debug("Logging in to Crestron Home at %s", self.base_url)
            
            try:
                # Create SSL context if not already created
                if self._ssl_context is None:
                    self._ssl_context = await self._create_ssl_context()
                
                # Make login request
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self._ssl_context)) as session:
                    headers = {
                        "Accept": "application/json",
                        "Crestron-RestAPI-AuthToken": self.api_token,
                    }
                    
                    async with session.get(
                        f"{self.base_url}/login",
                        headers=headers,
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()
                        
                        self.auth_key = data.get("AuthKey") or data.get("authkey")
                        if not self.auth_key:
                            raise CrestronAuthError("No authentication key received")
                        
                        self.last_login = current_time
                        _LOGGER.info(
                            "Successfully authenticated with Crestron Home, version: %s",
                            data.get("version", "unknown"),
                        )
            
            except ClientConnectorError as error:
                _LOGGER.error("Connection error: %s", error)
                raise CrestronConnectionError(f"Connection error: {error}") from error
            
            except ClientResponseError as error:
                _LOGGER.error("Authentication error: %s", error)
                raise CrestronAuthError(f"Authentication error: {error}") from error
            
            except Exception as error:
                _LOGGER.error("Unexpected error during login: %s", error)
                raise CrestronApiError(f"Unexpected error: {error}") from error

    async def _api_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an API request to the Crestron Home system."""
        await self.login()
        
        if not self.auth_key:
            raise CrestronAuthError("Not authenticated")
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Crestron-RestAPI-AuthKey": self.auth_key,
        }
        
        try:
            async with self._session.request(
                method, url, headers=headers, json=data
            ) as response:
                response.raise_for_status()
                return await response.json()
        
        except ClientResponseError as error:
            if error.status in (401, 511):
                # Force re-authentication on next request
                self.auth_key = None
                self.last_login = 0
                raise CrestronAuthError("Authentication expired") from error
            raise CrestronApiError(f"API error: {error}") from error
        
        except Exception as error:
            _LOGGER.error("API request error: %s", error)
            raise CrestronApiError(f"API request error: {error}") from error

    async def get_devices(self, enabled_types: List[str], ignored_device_names: List[str] = None) -> List[Dict[str, Any]]:
        """Get all devices from the Crestron Home system."""
        _LOGGER.debug("Getting devices from Crestron Home with enabled types: %s", enabled_types)
        
        # Get ignored device names from environment if not provided
        if ignored_device_names is None:
            ignored_device_names_str = os.environ.get("IGNORED_DEVICE_NAMES", "")
            if ignored_device_names_str:
                ignored_device_names = [name.strip() for name in ignored_device_names_str.split(",")]
            else:
                ignored_device_names = []
        
        _LOGGER.debug("Using ignored device name patterns: %s", ignored_device_names)
        
        try:
            # Get rooms, scenes, devices, lights, and shades in parallel
            results = await asyncio.gather(
                self._api_request("GET", "/rooms"),
                self._api_request("GET", "/scenes"),
                self._api_request("GET", "/devices"),
                self._api_request("GET", "/lights"),
                self._api_request("GET", "/shades"),
            )

            rooms_data = results[0]
            scenes_data = results[1]
            devices_data = results[2]
            lights_data = results[3]
            shades_data = results[4]

            # Store rooms for later use
            self.rooms = rooms_data.get("rooms", [])

            _LOGGER.debug("Found %d rooms, %d scenes, %d devices, %d lights, %d shades",
                         len(self.rooms),
                         len(scenes_data.get("scenes", [])),
                         len(devices_data.get("devices", [])),
                         len(lights_data.get("lights", [])),
                         len(shades_data.get("shades", [])))
            
            devices: List[Dict[str, Any]] = []
            
            # Build lookup maps for lights and shades data
            lights_by_id = {
                light.get("id"): light
                for light in lights_data.get("lights", [])
            }
            shades_by_id = {
                shade.get("id"): shade
                for shade in shades_data.get("shades", [])
            }

            # Process regular devices
            for device in devices_data.get("devices", []):
                room_name = next(
                    (r.get("name", "") for r in self.rooms if r.get("id") == device.get("roomId")),
                    "",
                )

                device_id = device.get("id")
                device_type = device.get("subType") or device.get("type", "")
                level = 0
                shade_position = 0
                connection_status = "online"

                if device_type in ("Dimmer", "Switch"):
                    # Merge level and connectionStatus from /lights endpoint
                    light = lights_by_id.get(device_id, {})
                    level = light.get("level", 0)
                    connection_status = light.get("connectionStatus", "online")
                elif device_type == "Shade":
                    # Merge position and connectionStatus from /shades endpoint
                    shade = shades_by_id.get(device_id, {})
                    shade_position = shade.get("position", 0)
                    connection_status = shade.get("connectionStatus", "online")

                # Map Crestron device types to Home Assistant device types
                ha_device_type = None
                if device_type in ("Dimmer", "Switch"):
                    ha_device_type = "light"
                elif device_type == "Shade":
                    ha_device_type = "shade"

                device_info = {
                    "id": device_id,
                    "type": device.get("type", ""),
                    "subType": device.get("subType") or device.get("type", ""),
                    "name": device.get("name", ""),
                    "roomId": device.get("roomId"),
                    "roomName": room_name,
                    "level": level,
                    "status": device.get("status", False),
                    "position": shade_position,
                    "connectionStatus": connection_status,
                    "ha_device_type": ha_device_type,
                }

                # Add all devices regardless of type or ignored pattern
                devices.append(device_info)
                _LOGGER.debug("Added %s device: %s (ID: %s)",
                             ha_device_type or "unknown", device_info["name"], device_info["id"])
            
            # Process scenes - add all scenes regardless of enabled_types or ignored patterns
            for scene in scenes_data.get("scenes", []):
                room_name = next(
                    (r.get("name", "") for r in self.rooms if r.get("id") == scene.get("roomId")),
                    "",
                )
                
                # Always set type to "Scene" regardless of the scene's type field
                # This ensures shade scenes are treated as scenes, not shades
                scene_info = {
                    "id": scene.get("id"),
                    "type": "Scene",
                    "subType": "Scene",  # Always use "Scene" as subType
                    "sceneType": scene.get("type", ""),  # Store original type as sceneType
                    "name": scene.get("name", ""),
                    "roomId": scene.get("roomId"),
                    "roomName": room_name,
                    "level": 0,
                    "status": scene.get("status", False),
                    "position": 0,
                    "connectionStatus": "n/a",  # Scenes don't have a physical connection status
                    "ha_device_type": "scene",
                }
                
                devices.append(scene_info)
                _LOGGER.debug("Added scene: %s (ID: %s, Type: %s)", 
                             scene_info["name"], scene_info["id"], scene_info["sceneType"])
            
            _LOGGER.info("Found %d devices matching enabled types", len(devices))
            return devices
        
        except Exception as error:
            _LOGGER.error("Error getting devices: %s", error)
            return []

    async def get_device(self, device_id: int) -> Dict[str, Any]:
        """Get a specific device from the Crestron Home system."""
        response = await self._api_request("GET", f"/devices/{device_id}")
        return response.get("devices", [{}])[0]

    async def get_shade_state(self, shade_id: int) -> Dict[str, Any]:
        """Get the state of a specific shade."""
        response = await self._api_request("GET", f"/shades/{shade_id}")
        return response.get("shades", [{}])[0]

    async def set_light_state(self, light_id: int, level: int, time: int = 0) -> None:
        """Set the state of a light."""
        light_state = {
            "lights": [
                {
                    "id": light_id,
                    "level": level,
                    "time": time,
                }
            ]
        }

        response = await self._api_request("POST", "/lights/SetState", light_state)
        status = response.get("status", "")
        if status == "failure":
            raise CrestronApiError(
                f"Failed to set light state: {response.get('errorMessage', 'Unknown error')}"
            )
        if status == "partial":
            _LOGGER.warning(
                "Partial light state update: %s (failed devices: %s)",
                response.get("errorMessage", ""),
                response.get("errorDevices", []),
            )

    async def set_shade_position(self, shade_id: int, position: int) -> None:
        """Set the position of a shade."""
        shade_state = {
            "shades": [
                {
                    "id": shade_id,
                    "position": position,
                }
            ]
        }

        response = await self._api_request("POST", "/shades/SetState", shade_state)
        status = response.get("status", "")
        if status == "failure":
            raise CrestronApiError(
                f"Failed to set shade position: {response.get('errorMessage', 'Unknown error')}"
            )
        if status == "partial":
            _LOGGER.warning(
                "Partial shade position update: %s (failed devices: %s)",
                response.get("errorMessage", ""),
                response.get("errorDevices", []),
            )

    async def execute_scene(self, scene_id: int) -> None:
        """Execute a scene."""
        response = await self._api_request("POST", f"/scenes/recall/{scene_id}", {})
        status = response.get("status", "")
        if status == "failure":
            raise CrestronApiError(
                f"Failed to execute scene: {response.get('errorMessage', 'Unknown error')}"
            )

    async def get_scene(self, scene_id: int) -> Dict[str, Any]:
        """Get a specific scene from the Crestron Home system."""
        response = await self._api_request("GET", f"/scenes/{scene_id}")
        return response.get("scenes", [{}])[0]

    async def get_sensors(self, ignored_device_names: List[str] = None) -> List[Dict[str, Any]]:
        """Get all sensors from the Crestron Home system."""
        # Get ignored device names from environment if not provided
        if ignored_device_names is None:
            ignored_device_names_str = os.environ.get("IGNORED_DEVICE_NAMES", "")
            if ignored_device_names_str:
                ignored_device_names = [name.strip() for name in ignored_device_names_str.split(",")]
            else:
                ignored_device_names = []
        
        response = await self._api_request("GET", "/sensors")
        sensors = response.get("sensors", [])
        
        # Return all sensors without filtering
        return sensors

    async def get_sensor(self, sensor_id: int) -> Dict[str, Any]:
        """Get a specific sensor from the Crestron Home system."""
        response = await self._api_request("GET", f"/sensors/{sensor_id}")
        return response.get("sensors", [{}])[0]

    async def get_rooms(self) -> List[Dict[str, Any]]:
        """Get all rooms from the Crestron Home system."""
        try:
            response = await self._api_request("GET", "/rooms")
            rooms = response.get("rooms", [])
            # Update the stored rooms data
            self.rooms = rooms
            return rooms
        except Exception as error:
            _LOGGER.error("Error getting rooms: %s", error)
            return []

    @staticmethod
    def crestron_to_percentage(value: int) -> int:
        """Convert a Crestron range value (0-65535) to percentage (0-100)."""
        if value <= 0:
            return 0
        return round((value / CRESTRON_MAX_LEVEL) * 100)

    @staticmethod
    def percentage_to_crestron(value: int) -> int:
        """Convert a percentage (0-100) to Crestron range value (0-65535)."""
        if value <= 0:
            return 0
        return round((CRESTRON_MAX_LEVEL * value) / 100)

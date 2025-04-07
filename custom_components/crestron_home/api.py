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
        
        # Create SSL context once during initialization to avoid blocking calls in the event loop
        self._ssl_context = ssl.create_default_context()
        self._ssl_context.check_hostname = False
        self._ssl_context.verify_mode = ssl.CERT_NONE

    async def login(self) -> None:
        """Login to the Crestron Home system."""
        # Check if we need to login (session expires after 10 minutes)
        current_time = time.time()
        if self.auth_key and (current_time - self.last_login) < CRESTRON_SESSION_TIMEOUT:
            _LOGGER.debug("Session is still valid, skipping login")
            return

        _LOGGER.debug("Logging in to Crestron Home at %s", self.base_url)
        
        try:
            # Use the pre-created SSL context
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
                    
                    self.auth_key = data.get("authkey")
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
            if error.status == 401:
                # Force re-authentication on next request
                self.auth_key = None
                self.last_login = 0
                raise CrestronAuthError("Authentication expired") from error
            raise CrestronApiError(f"API error: {error}") from error
        
        except Exception as error:
            _LOGGER.error("API request error: %s", error)
            raise CrestronApiError(f"API request error: {error}") from error

    def _matches_ignored_pattern(self, name: str, device_type: str, ignored_device_names: List[str]) -> bool:
        """Check if a device name or type matches any of the ignored patterns.
        
        Supports pattern matching with % wildcard:
        - bathroom → exact match
        - %bathroom → ends with bathroom
        - bathroom% → starts with bathroom
        - %bathroom% → contains bathroom
        """
        name = name.lower()
        device_type = device_type.lower()
        
        for pattern in ignored_device_names:
            pattern = pattern.lower()
            
            # Check for different pattern types
            if pattern.startswith("%") and pattern.endswith("%"):
                # %bathroom% → contains bathroom
                search_term = pattern[1:-1]
                if search_term in name or search_term in device_type:
                    return True
            elif pattern.startswith("%"):
                # %bathroom → ends with bathroom
                if name.endswith(pattern[1:]) or device_type.endswith(pattern[1:]):
                    return True
            elif pattern.endswith("%"):
                # bathroom% → starts with bathroom
                if name.startswith(pattern[:-1]) or device_type.startswith(pattern[:-1]):
                    return True
            else:
                # bathroom → exact match
                if name == pattern or device_type == pattern:
                    return True
        
        return False

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
            # Get rooms, scenes, devices, and shades in parallel
            results = await asyncio.gather(
                self._api_request("GET", "/rooms"),
                self._api_request("GET", "/scenes"),
                self._api_request("GET", "/devices"),
                self._api_request("GET", "/shades"),
            )
            
            rooms_data = results[0]
            scenes_data = results[1]
            devices_data = results[2]
            shades_data = results[3]
            
            # Store rooms for later use
            self.rooms = rooms_data.get("rooms", [])
            
            _LOGGER.debug("Found %d rooms, %d scenes, %d devices, %d shades", 
                         len(self.rooms), 
                         len(scenes_data.get("scenes", [])),
                         len(devices_data.get("devices", [])),
                         len(shades_data.get("shades", [])))
            
            devices: List[Dict[str, Any]] = []
            
            # Process regular devices
            for device in devices_data.get("devices", []):
                room_name = next(
                    (r.get("name", "") for r in self.rooms if r.get("id") == device.get("roomId")),
                    "",
                )
                
                device_type = device.get("subType") or device.get("type", "")
                shade_position = 0
                
                if device_type == "Shade":
                    # Find matching shade position
                    for shade in shades_data.get("shades", []):
                        if shade.get("id") == device.get("id"):
                            shade_position = shade.get("position", 0)
                            break
                
                # Map Crestron device types to Home Assistant device types
                ha_device_type = None
                if device_type == "Dimmer" or device_type == "Switch":
                    ha_device_type = "light"
                elif device_type == "Shade":
                    ha_device_type = "shade"
                
                device_info = {
                    "id": device.get("id"),
                    "type": device_type,
                    "subType": device_type,
                    "name": f"{room_name} {device.get('name', '')}",
                    "roomId": device.get("roomId"),
                    "roomName": room_name,
                    "level": device.get("level", 0),
                    "status": device.get("status", False),
                    "position": shade_position,
                    "connectionStatus": device.get("connectionStatus", "online"),
                    "ha_device_type": ha_device_type,
                }
                
                # Add device if its mapped type is in enabled_types and it doesn't match ignored patterns
                if ha_device_type and ha_device_type in enabled_types:
                    # Check if device matches any ignored pattern
                    if not self._matches_ignored_pattern(device_info['name'], device_type, ignored_device_names):
                        devices.append(device_info)
                        _LOGGER.debug("Added %s device: %s (ID: %s)", 
                                     ha_device_type, device_info["name"], device_info["id"])
                    else:
                        _LOGGER.debug("Skipped ignored device: %s (Type: %s)", 
                                     device_info["name"], device_type)
                else:
                    _LOGGER.debug("Skipped device: %s (Type: %s, Mapped Type: %s)", 
                                 device_info["name"], device_type, ha_device_type)
            
            # Process scenes
            if "scene" in enabled_types:
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
                        "name": f"{room_name} {scene.get('name', '')}",
                        "roomId": scene.get("roomId"),
                        "roomName": room_name,
                        "level": 0,
                        "status": scene.get("status", False),
                        "position": 0,
                        "connectionStatus": "n/a",  # Scenes don't have a physical connection status
                        "ha_device_type": "scene",
                    }
                    
                    # Check if scene matches any ignored pattern
                    if not self._matches_ignored_pattern(scene_info['name'], scene_info['sceneType'], ignored_device_names):
                        devices.append(scene_info)
                        _LOGGER.debug("Added scene: %s (ID: %s, Type: %s)", 
                                     scene_info["name"], scene_info["id"], scene_info["sceneType"])
                    else:
                        _LOGGER.debug("Skipped ignored scene: %s (Type: %s)", 
                                     scene_info["name"], scene_info["sceneType"])
            
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
        
        await self._api_request("POST", "/lights/setstate", light_state)

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
        
        await self._api_request("POST", "/shades/setstate", shade_state)

    async def execute_scene(self, scene_id: int) -> None:
        """Execute a scene."""
        await self._api_request("POST", f"/scenes/recall/{scene_id}", {})

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
        
        # If no ignored patterns, return all sensors
        if not ignored_device_names:
            return sensors
        
        # Filter out sensors that match ignored patterns
        filtered_sensors = []
        for sensor in sensors:
            # Get room name for the sensor
            room_name = ""
            room_id = sensor.get("roomId")
            if room_id:
                room_name = next(
                    (r.get("name", "") for r in self.rooms if r.get("id") == room_id),
                    "",
                )
            
            sensor_name = f"{room_name} {sensor.get('name', '')}".strip()
            sensor_type = sensor.get("subType", "")
            
            # Check if sensor matches any ignored pattern
            if not self._matches_ignored_pattern(sensor_name, sensor_type, ignored_device_names):
                filtered_sensors.append(sensor)
            else:
                _LOGGER.debug("Skipped ignored sensor: %s (Type: %s)", 
                             sensor_name, sensor_type)
        
        return filtered_sensors

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

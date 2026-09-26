"""API Client for Crestron Home."""
import asyncio
import logging
import ssl
import time
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError, ClientResponseError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CRESTRON_API_PATH,
    CRESTRON_MAX_LEVEL,
    CRESTRON_SESSION_TIMEOUT,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_SCENE,
    DEVICE_TYPE_SHADE,
)

_LOGGER = logging.getLogger(__name__)
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)
_ROOM_CACHE_TTL = 300


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
        self._rooms_expire_at = 0.0
        self._session = async_get_clientsession(hass, verify_ssl=False)
        self._ssl_context = None
        
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
        current_time = time.time()
        if self.auth_key and (current_time - self.last_login) < CRESTRON_SESSION_TIMEOUT:
            _LOGGER.debug("Session is still valid, skipping login")
            return

        async with self._login_lock:
            # Another request may have logged in while this one waited for the lock.
            current_time = time.time()
            if self.auth_key and (current_time - self.last_login) < CRESTRON_SESSION_TIMEOUT:
                _LOGGER.debug("Session is still valid, skipping login (after lock)")
                return
                
            _LOGGER.debug("Logging in to Crestron Home at %s", self.base_url)
            
            try:
                if self._ssl_context is None:
                    self._ssl_context = await self._create_ssl_context()
                
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self._ssl_context)) as session:
                    headers = {
                        "Accept": "application/json",
                        "Crestron-RestAPI-AuthToken": self.api_token,
                    }
                    
                    async with session.get(
                        f"{self.base_url}/login",
                        headers=headers,
                        timeout=_REQUEST_TIMEOUT,
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
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        *,
        retry_on_disconnect: bool = False,
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
            while True:
                try:
                    async with self._session.request(
                        method, url, headers=headers, json=data,
                        timeout=_REQUEST_TIMEOUT,
                    ) as response:
                        response.raise_for_status()
                        return await response.json()
                except aiohttp.ServerDisconnectedError:
                    if not retry_on_disconnect:
                        raise
                    retry_on_disconnect = False
                    _LOGGER.debug(
                        "Server disconnected during %s %s; retrying once",
                        method,
                        endpoint,
                    )
        
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

    async def _poll_endpoint(self, endpoint: str) -> dict[str, Any] | None:
        """Keep unavailable state distinct from a successful empty inventory."""
        try:
            return await self._api_request("GET", endpoint)
        except CrestronAuthError:
            raise
        except CrestronApiError as error:
            _LOGGER.warning("Could not poll %s: %s", endpoint, error)
            return None

    async def get_devices(
        self, enabled_types: list[str],
    ) -> tuple[list[dict[str, Any]], set[str]]:
        """Return discovered state and categories whose endpoints failed."""
        endpoints = {
            device_type: endpoint
            for device_type, endpoint in (
                (DEVICE_TYPE_LIGHT, "lights"),
                (DEVICE_TYPE_SHADE, "shades"),
                (DEVICE_TYPE_SCENE, "scenes"),
            )
            if device_type in enabled_types
        }
        results = await asyncio.gather(
            self.get_rooms(),
            self._api_request("GET", "/devices"),
            *(self._poll_endpoint(f"/{endpoint}") for endpoint in endpoints.values()),
        )
        responses = dict(zip(endpoints, results[2:], strict=True))
        failed_types = {kind for kind, data in responses.items() if data is None}
        devices_data = results[1]
        lights_data = responses.get(DEVICE_TYPE_LIGHT) or {}
        shades_data = responses.get(DEVICE_TYPE_SHADE) or {}
        scenes_data = responses.get(DEVICE_TYPE_SCENE) or {}

        _LOGGER.debug("Found %d rooms, %d scenes, %d devices, %d lights, %d shades",
                     len(self.rooms),
                     len(scenes_data.get("scenes", [])),
                     len(devices_data.get("devices", [])),
                     len(lights_data.get("lights", [])),
                     len(shades_data.get("shades", [])))

        devices_by_id = {
            device["id"]: dict(device)
            for device in devices_data.get("devices", [])
            if device.get("id") is not None
        }
        for category, response in (("lights", lights_data), ("shades", shades_data)):
            for item in response.get(category, []):
                device_id = item.get("id")
                if device_id is None:
                    continue
                device = devices_by_id.setdefault(device_id, {})
                subtype = next(
                    (
                        value
                        for value in (
                            item.get("subType"), device.get("subType"),
                            item.get("type"), device.get("type"),
                        )
                        if value and value.lower() not in ("light", "shade")
                    ),
                    "",
                )
                device.update(item)
                # A level field implies dimming only when no explicit subtype exists;
                # switches also report a level.
                if not subtype:
                    if category == "shades":
                        subtype = "Shade"
                    else:
                        subtype = "Dimmer" if "level" in device else "Switch"
                device["subType"] = subtype

        room_names = {room["id"]: room.get("name", "") for room in self.rooms}
        device_types = {"Dimmer": "light", "Switch": "light", "Shade": "shade"}
        subtypes = {name.lower(): name for name in device_types}
        devices: list[dict[str, Any]] = []
        for device in devices_by_id.values():
            subtype = device.get("subType") or device.get("type", "")
            subtype = subtypes.get(subtype.lower(), subtype)
            device_type = device_types.get(subtype)
            # Do not replace failed state requests with generic identity stubs.
            if (
                device_type not in enabled_types
                or device_type in failed_types
            ):
                continue
            devices.append(
                {
                    **device,
                    "subType": subtype,
                    "roomName": room_names.get(device.get("roomId"), ""),
                    "ha_device_type": device_type,
                },
            )

        for scene in scenes_data.get("scenes", []):
            # Shade scenes must remain scenes rather than become cover entities.
            scene_info = {
                "id": scene.get("id"),
                "type": "Scene",
                "subType": "Scene",
                "sceneType": scene.get("type", ""),
                "name": scene.get("name", ""),
                "roomId": scene.get("roomId"),
                "roomName": room_names.get(scene.get("roomId"), ""),
                "level": 0,
                "status": scene.get("status", False),
                "position": 0,
                "connectionStatus": "n/a",  # Scenes have no physical connection.
                "ha_device_type": "scene",
            }

            devices.append(scene_info)
            _LOGGER.debug("Added scene: %s (ID: %s, Type: %s)",
                         scene_info["name"], scene_info["id"], scene_info["sceneType"])

        _LOGGER.debug("Found %d devices", len(devices))
        return devices, failed_types

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

        # Only replay instant settings: a lost response may hide success, and retrying a transition could restart its timer.
        response = await self._api_request(
            "POST", "/lights/SetState", light_state, retry_on_disconnect=time == 0,
        )
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

    async def get_sensors(self) -> list[dict[str, Any]] | None:
        """Return sensor state, or None when the endpoint is unavailable."""
        response = await self._poll_endpoint("/sensors")
        return response.get("sensors", []) if response is not None else None

    async def get_sensor(self, sensor_id: int) -> Dict[str, Any]:
        """Get a specific sensor from the Crestron Home system."""
        response = await self._api_request("GET", f"/sensors/{sensor_id}")
        return response.get("sensors", [{}])[0]

    async def get_rooms(self) -> List[Dict[str, Any]]:
        """Cache room definitions for five minutes, including empty inventories."""
        if time.monotonic() < self._rooms_expire_at:
            return self.rooms
        response = await self._api_request("GET", "/rooms")
        self.rooms = response.get("rooms", [])
        self._rooms_expire_at = time.monotonic() + _ROOM_CACHE_TTL
        return self.rooms

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

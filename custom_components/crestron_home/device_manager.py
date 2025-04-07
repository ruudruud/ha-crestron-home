"""Device manager for Crestron Home integration."""
import asyncio
import logging
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from homeassistant.core import HomeAssistant

from .api import CrestronApiError, CrestronClient

# Set to True to enable detailed device logging
DEBUG_MODE = True
from .const import (
    DEVICE_SUBTYPE_DOOR_SENSOR,
    DEVICE_SUBTYPE_OCCUPANCY_SENSOR,
    DEVICE_SUBTYPE_PHOTO_SENSOR,
    DEVICE_TYPE_BINARY_SENSOR,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_SCENE,
    DEVICE_TYPE_SENSOR,
    DEVICE_TYPE_SHADE,
)
from .models import CrestronDevice

_LOGGER = logging.getLogger(__name__)


class CrestronDeviceManager:
    """Manager for Crestron devices."""

    def _update_ha_parameters(self, device: CrestronDevice) -> None:
        """Update Home Assistant parameters based on device status.
        
        Logic:
        - All devices are registered in Home Assistant (ha_registry = True)
        - If device is functioning normally: state = available
        - If device is offline: state = unavailable
        """
        
        # Always register the device in Home Assistant
        device.ha_registry = True
        
        # Check connection status for availability
        if device.connection == "offline":
            device.ha_state = False  # Unavailable
            device.ha_reason = "Device is offline"
        else:
            device.ha_state = True  # Available
            device.ha_reason = ""  # No reason needed for normal operation

    def __init__(
        self,
        hass: HomeAssistant,
        client: CrestronClient,
        enabled_device_types: List[str],
        ignored_device_names: List[str] = None,
    ) -> None:
        """Initialize the device manager."""
        self.hass = hass
        self.client = client
        self.enabled_device_types = enabled_device_types
        self.ignored_device_names = ignored_device_names or []
        
        # Device storage
        self.devices: Dict[int, CrestronDevice] = {}
        self.previous_devices: Dict[int, CrestronDevice] = {}
        self.last_poll_time: Optional[datetime] = None
        
        # Mapping of Crestron device types to Home Assistant device types
        self.device_type_mapping = {
            "Dimmer": DEVICE_TYPE_LIGHT,
            "Switch": DEVICE_TYPE_LIGHT,
            "Shade": DEVICE_TYPE_SHADE,
            "Scene": DEVICE_TYPE_SCENE,
            "OccupancySensor": DEVICE_TYPE_BINARY_SENSOR,
            "DoorSensor": DEVICE_TYPE_BINARY_SENSOR,
            "PhotoSensor": DEVICE_TYPE_SENSOR,
        }

    def _matches_ignored_pattern(self, name: str, device_type: str) -> bool:
        """Check if a device name or type matches any of the ignored patterns.
        
        Supports pattern matching with % wildcard:
        - bathroom → exact match
        - %bathroom → ends with bathroom
        - bathroom% → starts with bathroom
        - %bathroom% → contains bathroom
        """
        if not self.ignored_device_names:
            return False
            
        name = name.lower()
        device_type = device_type.lower()
        
        for pattern in self.ignored_device_names:
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

    async def poll_devices(self) -> Dict[str, List[CrestronDevice]]:
        """Poll devices from the Crestron Home system and update the device snapshot."""
        try:
            _LOGGER.debug("Polling devices with enabled types: %s", self.enabled_device_types)
            
            # Store previous devices for future change detection
            self.previous_devices = deepcopy(self.devices)
            
            # Get all devices and sensors from the Crestron Home system
            results = await asyncio.gather(
                self.client.get_devices(self.enabled_device_types, self.ignored_device_names),
                self.client.get_sensors(self.ignored_device_names),
            )
            
            devices_data = results[0]
            sensors_data = results[1]
            
            _LOGGER.debug("Received %d devices and %d sensors from API", 
                         len(devices_data), len(sensors_data))
            
            # Process devices
            self._process_devices(devices_data)
            
            # Process sensors
            self._process_sensors(sensors_data)
            
            # Update last poll time
            self.last_poll_time = datetime.now()
            
            # TODO: Implement change detection logic here
            # This will compare self.devices with self.previous_devices
            
            # Organize devices by type for easier access
            devices_by_type = {
                DEVICE_TYPE_LIGHT: [],
                DEVICE_TYPE_SHADE: [],
                DEVICE_TYPE_SCENE: [],
                DEVICE_TYPE_BINARY_SENSOR: [],
                DEVICE_TYPE_SENSOR: [],
            }
            
            for device in self.devices.values():
                ha_device_type = self._get_ha_device_type(device.type, device.subtype)
                if ha_device_type and ha_device_type in devices_by_type:
                    devices_by_type[ha_device_type].append(device)
            
            # Log device counts by type
            for device_type, type_devices in devices_by_type.items():
                _LOGGER.info("Found %d devices for %s platform", len(type_devices), device_type)
            
            # Log detailed device information if debug mode is enabled
            if DEBUG_MODE:
                self._log_device_snapshot()
            
            return devices_by_type
        
        except CrestronApiError as error:
            _LOGGER.error("Error polling devices: %s", error)
            return {
                DEVICE_TYPE_LIGHT: [],
                DEVICE_TYPE_SHADE: [],
                DEVICE_TYPE_SCENE: [],
                DEVICE_TYPE_BINARY_SENSOR: [],
                DEVICE_TYPE_SENSOR: [],
            }

    def _process_devices(self, devices_data: List[Dict[str, Any]]) -> None:
        """Process device data from the API and update the device snapshot."""
        for device_data in devices_data:
            device_id = device_data.get("id")
            if not device_id:
                continue
                
            device_type = device_data.get("subType") or device_data.get("type", "")
            ha_device_type = self._get_ha_device_type(device_type, device_type)
            
            # Process all devices regardless of type
                
            # Get room information
            room_id = device_data.get("roomId")
            room_name = device_data.get("roomName", "")
            
            # Create or update device
            if device_id in self.devices:
                # Update existing device
                device = self.devices[device_id]
                device.status = device_data.get("status", False)
                device.level = device_data.get("level", 0)
                
                # Set appropriate connection status for update
                # Scenes don't have a physical connection status
                if device_type == "Scene":
                    device.connection = "n/a"
                else:
                    device.connection = device_data.get("connectionStatus", "online")
                
                device.last_updated = datetime.now()
                
                # Update position for shades
                if device_type == "Shade":
                    device.position = device_data.get("position", 0)
                
                # Update raw data
                device.raw_data = device_data
                
                # Update Home Assistant parameters
                self._update_ha_parameters(device)
            else:
                # Set appropriate connection status
                # Scenes don't have a physical connection status
                connection_status = "n/a" if device_type == "Scene" else device_data.get("connectionStatus", "online")
                
                # Create new device
                device = CrestronDevice(
                    id=device_id,
                    room=room_name,
                    name=device_data.get("name", ""),
                    type=device_type,
                    subtype=device_type,
                    status=device_data.get("status", False),
                    level=device_data.get("level", 0),
                    connection=connection_status,
                    room_id=room_id,
                    position=device_data.get("position", 0) if device_type == "Shade" else 0,
                    raw_data=device_data,
                )
                
                # Add to devices dictionary
                self.devices[device_id] = device
                
                # Update Home Assistant parameters
                self._update_ha_parameters(device)

    def _process_sensors(self, sensors_data: List[Dict[str, Any]]) -> None:
        """Process sensor data from the API and update the device snapshot."""
        for sensor_data in sensors_data:
            sensor_id = sensor_data.get("id")
            if not sensor_id:
                continue
                
            sensor_type = sensor_data.get("subType", "")
            ha_device_type = None
            
            # Determine sensor type
            if sensor_type == DEVICE_SUBTYPE_OCCUPANCY_SENSOR:
                ha_device_type = DEVICE_TYPE_BINARY_SENSOR
            elif sensor_type == DEVICE_SUBTYPE_DOOR_SENSOR:
                ha_device_type = DEVICE_TYPE_BINARY_SENSOR
            elif sensor_type == DEVICE_SUBTYPE_PHOTO_SENSOR:
                ha_device_type = DEVICE_TYPE_SENSOR
            
            # Process all sensors regardless of type
                
            # Get room information
            room_id = sensor_data.get("roomId")
            room_name = ""
            if room_id:
                room_name = next(
                    (r.get("name", "") for r in self.client.rooms if r.get("id") == room_id),
                    "",
                )
            
            # Create sensor name
            sensor_name = f"{room_name} {sensor_data.get('name', '')}".strip()
            
            # Process all sensors regardless of ignored patterns
            
            # Create or update sensor
            if sensor_id in self.devices:
                # Update existing sensor
                sensor = self.devices[sensor_id]
                sensor.connection = sensor_data.get("connectionStatus", "online")
                sensor.last_updated = datetime.now()
                
                # Update sensor-specific properties
                if sensor_type == DEVICE_SUBTYPE_OCCUPANCY_SENSOR:
                    sensor.presence = sensor_data.get("presence", "Unavailable")
                    sensor.status = sensor_data.get("presence", "Unavailable") not in ["Vacant", "Unavailable"]
                elif sensor_type == DEVICE_SUBTYPE_DOOR_SENSOR:
                    sensor.door_status = sensor_data.get("door_status", "Closed")
                    sensor.battery_level = sensor_data.get("battery_level", "Normal")
                    sensor.status = sensor_data.get("door_status", "Closed") == "Open"
                elif sensor_type == DEVICE_SUBTYPE_PHOTO_SENSOR:
                    sensor.value = sensor_data.get("level", 0)
                    sensor.level = sensor_data.get("level", 0)
                
                # Update raw data
                sensor.raw_data = sensor_data
                
                # Update Home Assistant parameters
                self._update_ha_parameters(sensor)
            else:
                # Create new sensor
                sensor = CrestronDevice(
                    id=sensor_id,
                    room=room_name,
                    name=sensor_data.get("name", ""),
                    type=sensor_type,
                    subtype=sensor_type,
                    connection=sensor_data.get("connectionStatus", "online"),
                    room_id=room_id,
                    raw_data=sensor_data,
                )
                
                # Set sensor-specific properties
                if sensor_type == DEVICE_SUBTYPE_OCCUPANCY_SENSOR:
                    sensor.presence = sensor_data.get("presence", "Unavailable")
                    sensor.status = sensor_data.get("presence", "Unavailable") not in ["Vacant", "Unavailable"]
                elif sensor_type == DEVICE_SUBTYPE_DOOR_SENSOR:
                    sensor.door_status = sensor_data.get("door_status", "Closed")
                    sensor.battery_level = sensor_data.get("battery_level", "Normal")
                    sensor.status = sensor_data.get("door_status", "Closed") == "Open"
                elif sensor_type == DEVICE_SUBTYPE_PHOTO_SENSOR:
                    sensor.value = sensor_data.get("level", 0)
                    sensor.level = sensor_data.get("level", 0)
                
                # Add to devices dictionary
                self.devices[sensor_id] = sensor
                
                # Update Home Assistant parameters
                self._update_ha_parameters(sensor)

    def _get_ha_device_type(self, device_type: str, subtype: str) -> Optional[str]:
        """Map Crestron device type to Home Assistant device type."""
        # Try to get from mapping
        ha_type = self.device_type_mapping.get(subtype) or self.device_type_mapping.get(device_type)
        
        # Special case for scenes
        if device_type == "Scene" or subtype == "Scene":
            return DEVICE_TYPE_SCENE
        
        return ha_type

    def get_device(self, device_id: int) -> Optional[CrestronDevice]:
        """Get a device by ID."""
        return self.devices.get(device_id)

    def get_devices_by_type(self, device_type: str) -> List[CrestronDevice]:
        """Get all devices of a specific type."""
        return [
            device for device in self.devices.values()
            if self._get_ha_device_type(device.type, device.subtype) == device_type
        ]

    def get_devices_by_room(self, room_id: int) -> List[CrestronDevice]:
        """Get all devices in a specific room."""
        return [
            device for device in self.devices.values()
            if device.room_id == room_id
        ]

    def get_all_devices(self) -> List[CrestronDevice]:
        """Get all devices."""
        return list(self.devices.values())

    def _log_device_snapshot(self) -> None:
        """Log a detailed snapshot of all devices for debugging."""
        if not self.devices:
            _LOGGER.info("No devices found to log")
            return
        
        # Group devices by room for better readability
        devices_by_room: Dict[str, List[CrestronDevice]] = {}
        for device in self.devices.values():
            room_name = device.room or "Unknown Room"
            if room_name not in devices_by_room:
                devices_by_room[room_name] = []
            devices_by_room[room_name].append(device)
        
        # Log header
        _LOGGER.info("=" * 80)
        _LOGGER.info("CRESTRON DEVICE SNAPSHOT")
        _LOGGER.info("=" * 80)
        _LOGGER.info("Total devices: %d", len(self.devices))
        _LOGGER.info("Last updated: %s", self.last_poll_time.isoformat() if self.last_poll_time else "Never")
        _LOGGER.info("=" * 80)
        
        # Log devices by room
        for room_name, room_devices in sorted(devices_by_room.items()):
            _LOGGER.info("")
            _LOGGER.info("ROOM: %s (%d devices)", room_name, len(room_devices))
            _LOGGER.info("-" * 80)
            
            # Sort devices by type and name
            room_devices.sort(key=lambda d: (d.type, d.name))
            
            for device in room_devices:
                # Log basic device information
                _LOGGER.info("DEVICE: %s (ID: %d)", device.full_name, device.id)
                _LOGGER.info("  Type: %s / Subtype: %s", device.type, device.subtype)
                _LOGGER.info("  Status: %s / Level: %d", "ON" if device.status else "OFF", device.level)
                _LOGGER.info("  Connection: %s / Last Updated: %s", 
                            device.connection, device.last_updated.isoformat())
                _LOGGER.info("  Availability reason: %s / HA State: %s / HA Registry: %s",
                            device.ha_reason or "None", device.ha_state, device.ha_registry)
                
                # Log device-specific properties
                if device.type == "Shade" or device.subtype == "Shade":
                    _LOGGER.info("  Position: %d", device.position)
                
                if device.subtype == DEVICE_SUBTYPE_OCCUPANCY_SENSOR:
                    _LOGGER.info("  Presence: %s", device.presence)
                
                if device.subtype == DEVICE_SUBTYPE_DOOR_SENSOR:
                    _LOGGER.info("  Door Status: %s / Battery Level: %s", 
                                device.door_status, device.battery_level)
                
                if device.subtype == DEVICE_SUBTYPE_PHOTO_SENSOR:
                    _LOGGER.info("  Value: %s / Unit: %s", 
                                device.value, device.unit or "None")
                
                _LOGGER.info("-" * 80)
        
        _LOGGER.info("=" * 80)
        _LOGGER.info("END OF DEVICE SNAPSHOT")
        _LOGGER.info("=" * 80)

    def get_device_snapshot(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get a snapshot of all devices for debugging."""
        snapshot = {
            "lights": [],
            "shades": [],
            "scenes": [],
            "binary_sensors": [],
            "sensors": [],
        }
        
        for device in self.devices.values():
            ha_device_type = self._get_ha_device_type(device.type, device.subtype)
            
            device_data = {
                "id": device.id,
                "name": device.full_name,
                "type": device.type,
                "subtype": device.subtype,
                "status": device.status,
                "level": device.level,
                "connection": device.connection,
                "last_updated": device.last_updated.isoformat(),
                "ha_registry": device.ha_registry,
                "ha_state": device.ha_state,
                "ha_reason": device.ha_reason,
            }
            
            # Add device type specific data
            if device.type == "Shade" or device.subtype == "Shade":
                device_data["position"] = device.position
                snapshot["shades"].append(device_data)
            elif ha_device_type == DEVICE_TYPE_LIGHT:
                snapshot["lights"].append(device_data)
            elif ha_device_type == DEVICE_TYPE_SCENE:
                snapshot["scenes"].append(device_data)
            elif ha_device_type == DEVICE_TYPE_BINARY_SENSOR:
                if device.subtype == DEVICE_SUBTYPE_OCCUPANCY_SENSOR:
                    device_data["presence"] = device.presence
                elif device.subtype == DEVICE_SUBTYPE_DOOR_SENSOR:
                    device_data["door_status"] = device.door_status
                    device_data["battery_level"] = device.battery_level
                snapshot["binary_sensors"].append(device_data)
            elif ha_device_type == DEVICE_TYPE_SENSOR:
                if device.subtype == DEVICE_SUBTYPE_PHOTO_SENSOR:
                    device_data["value"] = device.value
                snapshot["sensors"].append(device_data)
        
        return snapshot

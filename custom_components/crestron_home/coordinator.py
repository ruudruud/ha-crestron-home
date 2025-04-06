"""DataUpdateCoordinator for Crestron Home integration."""
import asyncio
from datetime import timedelta
import logging
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import CrestronApiError, CrestronAuthError, CrestronClient, CrestronConnectionError
from .const import (
    DEVICE_SUBTYPE_DOOR_SENSOR,
    DEVICE_SUBTYPE_OCCUPANCY_SENSOR,
    DEVICE_SUBTYPE_PHOTO_SENSOR,
    DEVICE_TYPE_BINARY_SENSOR,
    DEVICE_TYPE_SENSOR,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class CrestronHomeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Crestron Home system."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: CrestronClient,
        update_interval: int,
        enabled_device_types: List[str],
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.enabled_device_types = enabled_device_types
        self.devices: List[Dict[str, Any]] = []
        self.platforms = []
        
        # Add counter for room updates
        self.update_counter = 0
        self.room_update_frequency = 10  # Check room names every 10 cycles
        
        # Store room name mapping for change detection
        self.room_names = {}  # room_id -> room_name mapping
        
        # Store entity references for name updates
        self.entities = []

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via API client."""
        try:
            # Increment counter
            self.update_counter += 1
            
            # Check if it's time to refresh room data
            refresh_rooms = (self.update_counter % self.room_update_frequency == 0)
            
            _LOGGER.debug("Updating data with enabled device types: %s", self.enabled_device_types)
            
            # Get all devices and sensors from the Crestron Home system
            results = await asyncio.gather(
                self.client.get_devices(self.enabled_device_types),
                self.client.get_sensors(),
            )
            
            # Check for room name changes if needed
            if refresh_rooms:
                await self._refresh_room_names()
            
            self.devices = results[0]
            sensors_data = results[1]
            
            _LOGGER.debug("Received %d devices and %d sensors from API", 
                         len(self.devices), len(sensors_data))
            
            # Organize devices by type for easier access
            devices_by_type = {
                "light": [],
                "shade": [],
                "scene": [],
                "binary_sensor": [],
                "sensor": [],
            }
            
            for device in self.devices:
                # Use the mapped Home Assistant device type
                ha_device_type = device.get("ha_device_type")
                
                if ha_device_type and ha_device_type in devices_by_type:
                    devices_by_type[ha_device_type].append(device)
                    _LOGGER.debug("Added device to %s platform: %s", ha_device_type, device.get("name"))
            
            # Process sensors
            if DEVICE_TYPE_BINARY_SENSOR in self.enabled_device_types or DEVICE_TYPE_SENSOR in self.enabled_device_types:
                for sensor in sensors_data:
                    # Get room name for the sensor
                    room_name = ""
                    room_id = sensor.get("roomId")
                    if room_id:
                        room_name = next(
                            (r.get("name", "") for r in self.client.rooms if r.get("id") == room_id),
                            "",
                        )
                    
                    # Determine sensor type based on subType
                    sub_type = sensor.get("subType", "")
                    ha_device_type = None
                    
                    if sub_type == DEVICE_SUBTYPE_OCCUPANCY_SENSOR:
                        ha_device_type = DEVICE_TYPE_BINARY_SENSOR
                    elif sub_type == DEVICE_SUBTYPE_DOOR_SENSOR:
                        ha_device_type = DEVICE_TYPE_BINARY_SENSOR
                    elif sub_type == DEVICE_SUBTYPE_PHOTO_SENSOR:
                        ha_device_type = DEVICE_TYPE_SENSOR
                    
                    if ha_device_type and ha_device_type in self.enabled_device_types:
                        # Create sensor info
                        sensor_name = f"{room_name} {sensor.get('name', '')}".strip()
                        
                        # Skip sensors with 'Circadian' in the name (case insensitive)
                        if 'circadian' in sensor_name.lower() or 'circadian' in sub_type.lower():
                            _LOGGER.debug("Skipped Circadian sensor: %s (Type: %s)", 
                                         sensor_name, sub_type)
                            continue
                        
                        sensor_info = {
                            "id": sensor.get("id"),
                            "type": sub_type,
                            "subType": sub_type,
                            "name": sensor_name,
                            "roomId": room_id,
                            "roomName": room_name,
                            "ha_device_type": ha_device_type,
                        }
                        
                        # Add sensor-specific properties
                        if sub_type == DEVICE_SUBTYPE_OCCUPANCY_SENSOR:
                            sensor_info["presence"] = sensor.get("presence", "Unavailable")
                        elif sub_type == DEVICE_SUBTYPE_DOOR_SENSOR:
                            sensor_info["door_status"] = sensor.get("door_status", "Closed")
                            sensor_info["battery_level"] = sensor.get("battery_level", "Normal")
                        elif sub_type == DEVICE_SUBTYPE_PHOTO_SENSOR:
                            sensor_info["level"] = sensor.get("level", 0)
                        
                        # Add to devices_by_type
                        devices_by_type[ha_device_type].append(sensor_info)
                        _LOGGER.debug("Added sensor to %s platform: %s (Type: %s)", 
                                     ha_device_type, sensor_info["name"], sub_type)
            
            # Log device counts by type
            for device_type, type_devices in devices_by_type.items():
                _LOGGER.info("Found %d devices for %s platform", len(type_devices), device_type)
            
            return devices_by_type
        
        except CrestronConnectionError as error:
            raise UpdateFailed(f"Connection error: {error}")
        
        except CrestronAuthError as error:
            raise UpdateFailed(f"Authentication error: {error}")
        
        except CrestronApiError as error:
            raise UpdateFailed(f"API error: {error}")
        
        except Exception as error:
            raise UpdateFailed(f"Unexpected error: {error}")
            
    async def _refresh_room_names(self) -> None:
        """Refresh room names and update entities if needed."""
        try:
            # Fetch latest room data
            rooms = await self.client.get_rooms()
            
            # Create new room_id -> name mapping
            new_room_names = {room.get("id"): room.get("name", "") for room in rooms}
            
            # Check for changes
            room_changes = {}
            for room_id, new_name in new_room_names.items():
                old_name = self.room_names.get(room_id)
                if old_name is not None and old_name != new_name:
                    room_changes[room_id] = (old_name, new_name)
                    _LOGGER.info(
                        "Room name changed: %s -> %s (ID: %s)",
                        old_name, new_name, room_id
                    )
            
            # Update stored room names
            self.room_names = new_room_names
            
            # If we have changes and registered entities, update them
            if room_changes and self.entities:
                for entity in self.entities:
                    if hasattr(entity, "room_id") and entity.room_id in room_changes:
                        await entity.async_update_room_name(room_changes[entity.room_id][1])
        
        except Exception as error:
            _LOGGER.error("Error refreshing room names: %s", error)
    
    def register_entity(self, entity) -> None:
        """Register an entity for room name updates."""
        if entity not in self.entities:
            self.entities.append(entity)
            
            # Store initial room name if available
            if hasattr(entity, "room_id") and entity.room_id is not None:
                room_name = entity._device_info.get("roomName", "")
                if room_name:
                    self.room_names[entity.room_id] = room_name

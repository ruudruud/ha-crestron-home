"""Entity base classes for Crestron Home integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)


class CrestronRoomEntity:
    """Mixin for Crestron entities that belong to a room."""
    
    @property
    def room_id(self) -> Optional[int]:
        """Return the room ID for this entity."""
        return self._device_info.get("roomId")
    
    async def async_update_room_name(self, new_room_name: str) -> None:
        """Update the entity name when room name changes."""
        # Get device name without room prefix
        device_name = self._device_info.get("name", "")
        old_room_name = self._device_info.get("roomName", "")
        
        if old_room_name and device_name.startswith(old_room_name):
            # Extract the device-specific part of the name
            device_part = device_name[len(old_room_name):].strip()
            # Create new name with updated room name
            new_name = f"{new_room_name} {device_part}"
            
            _LOGGER.info(
                "Updating entity name: %s -> %s (Room: %s -> %s)",
                device_name, new_name, old_room_name, new_room_name
            )
            
            # Update stored device info
            self._device_info["name"] = new_name
            self._device_info["roomName"] = new_room_name
            
            # Schedule update to refresh entity name in HA
            self.async_schedule_update_ha_state()

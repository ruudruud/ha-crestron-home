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

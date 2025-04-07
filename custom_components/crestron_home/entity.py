"""Entity base classes for Crestron Home integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.helpers.entity import Entity

from .models import CrestronDevice

_LOGGER = logging.getLogger(__name__)


class CrestronRoomEntity:
    """Mixin for Crestron entities that belong to a room."""
    
    @property
    def room_id(self) -> Optional[int]:
        """Return the room ID for this entity."""
        if isinstance(self._device_info, CrestronDevice):
            return self._device_info.room_id
        return None

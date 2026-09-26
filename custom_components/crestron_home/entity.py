"""Entity base classes for Crestron Home integration."""
from __future__ import annotations

from homeassistant.helpers import entity_registry as er

from .models import CrestronDevice


class CrestronRoomEntity:
    """Mixin for Crestron entities that belong to a room."""

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        registry = er.async_get(self.hass)
        entry = registry.async_get(self.entity_id)
        if entry is None or entry.hidden_by == er.RegistryEntryHider.USER:
            return

        hidden_by = (
            er.RegistryEntryHider.INTEGRATION if self._device.ha_hidden else None
        )
        if entry.hidden_by != hidden_by:
            registry.async_update_entity(self.entity_id, hidden_by=hidden_by)

    @property
    def room_id(self) -> int | None:
        """Return the room ID for this entity."""
        if isinstance(self._device_info, CrestronDevice):
            return self._device_info.room_id
        return None

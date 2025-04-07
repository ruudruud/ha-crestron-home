"""Support for Crestron Home scenes."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENABLED_DEVICE_TYPES,
    DEVICE_SUBTYPE_SCENE,
    DEVICE_TYPE_SCENE,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import CrestronHomeDataUpdateCoordinator
from .entity import CrestronRoomEntity
from .models import CrestronDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Crestron Home scenes based on config entry."""
    coordinator: CrestronHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Check if scene platform is enabled
    enabled_device_types = entry.data.get(CONF_ENABLED_DEVICE_TYPES, [])
    if DEVICE_TYPE_SCENE not in enabled_device_types:
        _LOGGER.debug("Scene platform not enabled, skipping setup")
        return
    
    # Get all scene devices from the coordinator
    scenes = []
    
    for device in coordinator.data.get(DEVICE_TYPE_SCENE, []):
        scenes.append(CrestronHomeScene(coordinator, device))
    
    _LOGGER.debug("Adding %d scene entities", len(scenes))
    async_add_entities(scenes)


class CrestronHomeScene(CrestronRoomEntity, Scene):
    """Representation of a Crestron Home scene."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: CrestronDevice,
    ) -> None:
        """Initialize the scene."""
        self.coordinator = coordinator
        self._device_info = device  # Store as _device_info for CrestronRoomEntity
        self._device = device  # Keep _device for backward compatibility
        self._attr_unique_id = f"crestron_scene_{device.id}"
        self._attr_name = device.full_name
        self._attr_has_entity_name = False
        
        # Set up device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device.id))},
            name=device.full_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            via_device=(DOMAIN, coordinator.client.host),
            suggested_area=device.room,
        )
    
    # Scenes are always available
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self.coordinator.client.execute_scene(self._device.id)
        
        # Request a coordinator update to get the new state
        await self.coordinator.async_request_refresh()
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for device in self.coordinator.data.get(DEVICE_TYPE_SCENE, []):
            if device.id == self._device.id:
                self._device = device
                self._device_info = device  # Update _device_info for CrestronRoomEntity
                break
        
        self.async_write_ha_state()

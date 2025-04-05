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


class CrestronHomeScene(Scene):
    """Representation of a Crestron Home scene."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: Dict[str, Any],
    ) -> None:
        """Initialize the scene."""
        self.coordinator = coordinator
        self._device = device
        self._attr_unique_id = f"crestron_scene_{device['id']}"
        self._attr_name = device["name"]
        self._attr_has_entity_name = True
        
        # Set up device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device["id"]))},
            name=device["name"],
            manufacturer=MANUFACTURER,
            model=MODEL,
            via_device=(DOMAIN, coordinator.client.host),
            suggested_area=device["roomName"],
        )
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # For scenes, we check if the device is in the coordinator data
        # Scenes don't have a connection status like physical devices,
        # but we can still check if they're in the latest data
        for device in self.coordinator.data.get(DEVICE_TYPE_SCENE, []):
            if device["id"] == self._device["id"]:
                # If the scene is in the latest data, it's available
                return True
        
        # If the scene is not found in the latest data, it's unavailable
        return False

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self.coordinator.client.execute_scene(self._device["id"])
        
        # Request a coordinator update to get the new state
        await self.coordinator.async_request_refresh()

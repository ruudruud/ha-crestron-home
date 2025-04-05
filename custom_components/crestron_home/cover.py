"""Support for Crestron Home covers (shades)."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.const import ATTR_ENTITY_PICTURE, Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import CrestronClient
from .const import (
    CONF_ENABLED_DEVICE_TYPES,
    DEVICE_SUBTYPE_SHADE,
    DEVICE_TYPE_SHADE,
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
    """Set up Crestron Home covers based on config entry."""
    coordinator: CrestronHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Check if shade platform is enabled
    enabled_device_types = entry.data.get(CONF_ENABLED_DEVICE_TYPES, [])
    if DEVICE_TYPE_SHADE not in enabled_device_types:
        _LOGGER.debug("Shade platform not enabled, skipping setup")
        return
    
    # Get all shade devices from the coordinator
    covers = []
    
    for device in coordinator.data.get(DEVICE_TYPE_SHADE, []):
        covers.append(CrestronHomeShade(coordinator, device))
    
    _LOGGER.debug("Adding %d cover entities", len(covers))
    async_add_entities(covers)


class CrestronHomeShade(CoordinatorEntity, CoverEntity):
    """Representation of a Crestron Home shade."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: Dict[str, Any],
    ) -> None:
        """Initialize the shade."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"crestron_shade_{device['id']}"
        self._attr_name = device["name"]
        self._attr_has_entity_name = True
        self._attr_device_class = CoverDeviceClass.SHADE
        
        # Support open, close, stop, and position
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        
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
    def current_cover_position(self) -> int:
        """Return current position of cover.
        
        0 is closed, 100 is fully open.
        """
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_SHADE, []):
            if device["id"] == self._device["id"]:
                return CrestronClient.crestron_to_percentage(device["position"])
        
        # If device not found, use the stored state
        return CrestronClient.crestron_to_percentage(self._device["position"])

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed."""
        return self.current_cover_position == 0

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.coordinator.client.set_shade_position(
            self._device["id"], CrestronClient.percentage_to_crestron(100)
        )
        
        # Request a coordinator update to get the new state
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.coordinator.client.set_shade_position(
            self._device["id"], 0
        )
        
        # Request a coordinator update to get the new state
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        # Get the current position and set it again to stop movement
        current_position = self.current_cover_position
        await self.coordinator.client.set_shade_position(
            self._device["id"], CrestronClient.percentage_to_crestron(current_position)
        )
        
        # Request a coordinator update to get the new state
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        if ATTR_POSITION in kwargs:
            position = kwargs[ATTR_POSITION]
            await self.coordinator.client.set_shade_position(
                self._device["id"], CrestronClient.percentage_to_crestron(position)
            )
            
            # Request a coordinator update to get the new state
            await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for device in self.coordinator.data.get(DEVICE_TYPE_SHADE, []):
            if device["id"] == self._device["id"]:
                self._device = device
                break
        
        self.async_write_ha_state()

"""Support for Crestron Home lights."""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import CrestronClient
from .const import (
    DEVICE_SUBTYPE_DIMMER,
    DEVICE_TYPE_LIGHT,
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
    """Set up Crestron Home lights based on config entry."""
    coordinator: CrestronHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Get all light devices from the coordinator
    lights = []
    
    for device in coordinator.data.get(DEVICE_TYPE_LIGHT, []):
        if device.get("type") == DEVICE_SUBTYPE_DIMMER:
            lights.append(CrestronHomeDimmer(coordinator, device))
        else:
            lights.append(CrestronHomeLight(coordinator, device))
    
    async_add_entities(lights)


class CrestronHomeBaseLight(CoordinatorEntity, LightEntity):
    """Representation of a Crestron Home light."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: Dict[str, Any],
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"crestron_light_{device['id']}"
        self._attr_name = device["name"]
        self._attr_has_entity_name = True
        self._attr_device_class = None
        
        # Set up device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device["id"]))},
            name=device["name"],
            manufacturer=MANUFACTURER,
            model=MODEL,
            via_device=(DOMAIN, coordinator.client.host),
        )

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_LIGHT, []):
            if device["id"] == self._device["id"]:
                return device["level"] > 0
        
        # If device not found, use the stored state
        return self._device["level"] > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        # Default to full brightness if not specified
        level = CrestronClient.percentage_to_crestron(100)
        
        await self.coordinator.client.set_light_state(
            self._device["id"], level
        )
        
        # Request a coordinator update to get the new state
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.coordinator.client.set_light_state(
            self._device["id"], 0
        )
        
        # Request a coordinator update to get the new state
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for device in self.coordinator.data.get(DEVICE_TYPE_LIGHT, []):
            if device["id"] == self._device["id"]:
                self._device = device
                break
        
        self.async_write_ha_state()


class CrestronHomeLight(CrestronHomeBaseLight):
    """Representation of a Crestron Home non-dimmable light."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: Dict[str, Any],
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator, device)
        self._attr_color_mode = ColorMode.ONOFF
        self._attr_supported_color_modes = {ColorMode.ONOFF}


class CrestronHomeDimmer(CrestronHomeBaseLight):
    """Representation of a Crestron Home dimmable light."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: Dict[str, Any],
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator, device)
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness of the light."""
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_LIGHT, []):
            if device["id"] == self._device["id"]:
                return int(CrestronClient.crestron_to_percentage(device["level"]) * 255 / 100)
        
        # If device not found, use the stored state
        return int(CrestronClient.crestron_to_percentage(self._device["level"]) * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        if ATTR_BRIGHTNESS in kwargs:
            # Convert Home Assistant brightness (0-255) to Crestron level (0-65535)
            brightness_pct = kwargs[ATTR_BRIGHTNESS] / 255 * 100
            level = CrestronClient.percentage_to_crestron(brightness_pct)
        else:
            # Default to full brightness if not specified
            level = CrestronClient.percentage_to_crestron(100)
        
        await self.coordinator.client.set_light_state(
            self._device["id"], level
        )
        
        # Request a coordinator update to get the new state
        await self.coordinator.async_request_refresh()

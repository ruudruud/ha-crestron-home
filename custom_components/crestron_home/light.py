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
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import CrestronClient
from .const import (
    CONF_ENABLED_DEVICE_TYPES,
    DEVICE_SUBTYPE_DIMMER,
    DEVICE_TYPE_LIGHT,
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
    """Set up Crestron Home lights based on config entry."""
    coordinator: CrestronHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Check if light platform is enabled
    enabled_device_types = entry.data.get(CONF_ENABLED_DEVICE_TYPES, [])
    if DEVICE_TYPE_LIGHT not in enabled_device_types:
        _LOGGER.debug("Light platform not enabled, skipping setup")
        return
    
    # Get all light devices from the coordinator
    lights = []
    
    for device in coordinator.data.get(DEVICE_TYPE_LIGHT, []):
        # Create the appropriate light entity
        if device.type == DEVICE_SUBTYPE_DIMMER:
            light = CrestronHomeDimmer(coordinator, device)
        else:
            light = CrestronHomeLight(coordinator, device)
        
        # Set hidden_by if device is marked as hidden
        if device.ha_hidden:
            light._attr_hidden_by = "integration"
            
        lights.append(light)
    
    _LOGGER.debug("Adding %d light entities", len(lights))
    async_add_entities(lights)


class CrestronHomeBaseLight(CrestronRoomEntity, CoordinatorEntity, LightEntity):
    """Representation of a Crestron Home light."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: CrestronDevice,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._device_info = device  # Store as _device_info for CrestronRoomEntity
        self._device = device  # Keep _device for backward compatibility
        self._attr_unique_id = f"crestron_light_{device.id}"
        self._attr_name = device.full_name
        self._attr_has_entity_name = False
        self._attr_device_class = None
        
        # Set up device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device.id))},
            name=device.full_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            via_device=(DOMAIN, coordinator.client.host),
            suggested_area=device.room,
        )
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_LIGHT, []):
            if device.id == self._device.id:
                return device.is_available
        
        # If device not found, use the stored state
        return self._device.is_available
        
    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        
        # Ensure hidden status is properly registered in the entity registry
        if self._device.ha_hidden:
            entity_registry = async_get_entity_registry(self.hass)
            if entry := entity_registry.async_get(self.entity_id):
                entity_registry.async_update_entity(
                    self.entity_id, 
                    hidden_by="integration"
                )

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_LIGHT, []):
            if device.id == self._device.id:
                return device.level > 0
        
        # If device not found, use the stored state
        return self._device.level > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        # Default to full brightness if not specified
        level = CrestronClient.percentage_to_crestron(100)
        
        await self.coordinator.client.set_light_state(
            self._device.id, level
        )
        
        # Request a coordinator update to get the new state
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.coordinator.client.set_light_state(
            self._device.id, 0
        )
        
        # Request a coordinator update to get the new state
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for device in self.coordinator.data.get(DEVICE_TYPE_LIGHT, []):
            if device.id == self._device.id:
                self._device = device
                self._device_info = device  # Update _device_info for CrestronRoomEntity
                break
        
        self.async_write_ha_state()


class CrestronHomeLight(CrestronHomeBaseLight):
    """Representation of a Crestron Home non-dimmable light."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: CrestronDevice,
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
        device: CrestronDevice,
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
            if device.id == self._device.id:
                return int(CrestronClient.crestron_to_percentage(device.level) * 255 / 100)
        
        # If device not found, use the stored state
        return int(CrestronClient.crestron_to_percentage(self._device.level) * 255 / 100)

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
            self._device.id, level
        )
        
        # Request a coordinator update to get the new state
        await self.coordinator.async_request_refresh()

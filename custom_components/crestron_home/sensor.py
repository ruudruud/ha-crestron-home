"""Support for Crestron Home sensors."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    LIGHT_LUX,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENABLED_DEVICE_TYPES,
    DEVICE_SUBTYPE_PHOTO_SENSOR,
    DEVICE_TYPE_SENSOR,
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
    """Set up Crestron Home sensors based on config entry."""
    coordinator: CrestronHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Check if sensor platform is enabled
    enabled_device_types = entry.data.get(CONF_ENABLED_DEVICE_TYPES, [])
    if DEVICE_TYPE_SENSOR not in enabled_device_types:
        _LOGGER.debug("Sensor platform not enabled, skipping setup")
        return
    
    # Get all sensor devices from the coordinator
    sensors = []
    
    for device in coordinator.data.get(DEVICE_TYPE_SENSOR, []):
        if device.get("subType") == DEVICE_SUBTYPE_PHOTO_SENSOR:
            sensors.append(CrestronHomePhotoSensor(coordinator, device))
    
    _LOGGER.debug("Adding %d sensor entities", len(sensors))
    async_add_entities(sensors)


class CrestronHomeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Crestron Home sensor."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: Dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"crestron_sensor_{device['id']}"
        self._attr_name = device["name"]
        self._attr_has_entity_name = False
        
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
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_SENSOR, []):
            if device["id"] == self._device["id"]:
                # If connectionStatus is not present or not "offline", consider it available
                return device.get("connectionStatus", "online") != "offline"
        
        # If device not found, use the stored state
        return self._device.get("connectionStatus", "online") != "offline"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for device in self.coordinator.data.get(DEVICE_TYPE_SENSOR, []):
            if device["id"] == self._device["id"]:
                self._device = device
                break
        
        self.async_write_ha_state()


class CrestronHomePhotoSensor(CrestronHomeSensor):
    """Representation of a Crestron Home photosensor."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: Dict[str, Any],
    ) -> None:
        """Initialize the photosensor."""
        super().__init__(coordinator, device)
        self._attr_device_class = SensorDeviceClass.ILLUMINANCE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = LIGHT_LUX
    
    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_SENSOR, []):
            if device["id"] == self._device["id"]:
                # Return the light level in lux
                return float(device.get("level", 0))
        
        # If device not found, use the stored state
        return float(self._device.get("level", 0))

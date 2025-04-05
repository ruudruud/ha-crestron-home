"""Support for Crestron Home binary sensors."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ENABLED_DEVICE_TYPES,
    DEVICE_SUBTYPE_DOOR_SENSOR,
    DEVICE_SUBTYPE_OCCUPANCY_SENSOR,
    DEVICE_TYPE_BINARY_SENSOR,
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
    """Set up Crestron Home binary sensors based on config entry."""
    coordinator: CrestronHomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Check if binary sensor platform is enabled
    enabled_device_types = entry.data.get(CONF_ENABLED_DEVICE_TYPES, [])
    if DEVICE_TYPE_BINARY_SENSOR not in enabled_device_types:
        _LOGGER.debug("Binary sensor platform not enabled, skipping setup")
        return
    
    # Get all binary sensor devices from the coordinator
    binary_sensors = []
    
    for device in coordinator.data.get(DEVICE_TYPE_BINARY_SENSOR, []):
        if device.get("subType") == DEVICE_SUBTYPE_OCCUPANCY_SENSOR:
            binary_sensors.append(CrestronHomeOccupancySensor(coordinator, device))
        elif device.get("subType") == DEVICE_SUBTYPE_DOOR_SENSOR:
            binary_sensors.append(CrestronHomeDoorSensor(coordinator, device))
    
    _LOGGER.debug("Adding %d binary sensor entities", len(binary_sensors))
    async_add_entities(binary_sensors)


class CrestronHomeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Crestron Home binary sensor."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: Dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"crestron_binary_sensor_{device['id']}"
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
        for device in self.coordinator.data.get(DEVICE_TYPE_BINARY_SENSOR, []):
            if device["id"] == self._device["id"]:
                # If connectionStatus is not present or not "offline", consider it available
                return device.get("connectionStatus", "online") != "offline"
        
        # If device not found, use the stored state
        return self._device.get("connectionStatus", "online") != "offline"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for device in self.coordinator.data.get(DEVICE_TYPE_BINARY_SENSOR, []):
            if device["id"] == self._device["id"]:
                self._device = device
                break
        
        self.async_write_ha_state()


class CrestronHomeOccupancySensor(CrestronHomeBinarySensor):
    """Representation of a Crestron Home occupancy sensor."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: Dict[str, Any],
    ) -> None:
        """Initialize the occupancy sensor."""
        super().__init__(coordinator, device)
        self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    
    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_BINARY_SENSOR, []):
            if device["id"] == self._device["id"]:
                # "Unavailable" means no occupancy, anything else means occupied
                return device.get("presence", "Unavailable") != "Unavailable"
        
        # If device not found, use the stored state
        return self._device.get("presence", "Unavailable") != "Unavailable"


class CrestronHomeDoorSensor(CrestronHomeBinarySensor):
    """Representation of a Crestron Home door sensor."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: Dict[str, Any],
    ) -> None:
        """Initialize the door sensor."""
        super().__init__(coordinator, device)
        self._attr_device_class = BinarySensorDeviceClass.DOOR
    
    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on (door is open)."""
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_BINARY_SENSOR, []):
            if device["id"] == self._device["id"]:
                # "Closed" means door is closed, "Open" means door is open
                return device.get("door_status", "Closed") == "Open"
        
        # If device not found, use the stored state
        return self._device.get("door_status", "Closed") == "Open"
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attributes = {}
        
        # Add battery level if available
        battery_level = None
        
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_BINARY_SENSOR, []):
            if device["id"] == self._device["id"]:
                battery_level = device.get("battery_level")
                break
        
        # If device not found, use the stored state
        if battery_level is None:
            battery_level = self._device.get("battery_level")
        
        if battery_level:
            attributes["battery_level"] = battery_level
        
        return attributes

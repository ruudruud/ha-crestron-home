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
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
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
from .entity import CrestronRoomEntity
from .models import CrestronDevice

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
        # Create the appropriate binary sensor entity
        if device.subtype == DEVICE_SUBTYPE_OCCUPANCY_SENSOR:
            sensor = CrestronHomeOccupancySensor(coordinator, device)
        elif device.subtype == DEVICE_SUBTYPE_DOOR_SENSOR:
            sensor = CrestronHomeDoorSensor(coordinator, device)
        else:
            continue  # Skip unknown sensor types
            
        # Set hidden_by if device is marked as hidden
        if device.ha_hidden:
            sensor._attr_hidden_by = "integration"
            
        binary_sensors.append(sensor)
    
    _LOGGER.debug("Adding %d binary sensor entities", len(binary_sensors))
    async_add_entities(binary_sensors)


class CrestronHomeBinarySensor(CrestronRoomEntity, CoordinatorEntity, BinarySensorEntity):
    """Representation of a Crestron Home binary sensor."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: CrestronDevice,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device_info = device  # Store as _device_info for CrestronRoomEntity
        self._device = device  # Keep _device for backward compatibility
        self._attr_unique_id = f"crestron_binary_sensor_{device.id}"
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
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_BINARY_SENSOR, []):
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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for device in self.coordinator.data.get(DEVICE_TYPE_BINARY_SENSOR, []):
            if device.id == self._device.id:
                self._device = device
                self._device_info = device  # Update _device_info for CrestronRoomEntity
                break
        
        self.async_write_ha_state()


class CrestronHomeOccupancySensor(CrestronHomeBinarySensor):
    """Representation of a Crestron Home occupancy sensor."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: CrestronDevice,
    ) -> None:
        """Initialize the occupancy sensor."""
        super().__init__(coordinator, device)
        self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    
    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_BINARY_SENSOR, []):
            if device.id == self._device.id:
                # "Vacant" or "Unavailable" means no occupancy, anything else means occupied
                return device.presence != "Vacant" and device.presence != "Unavailable"
        
        # If device not found, use the stored state
        return self._device.presence != "Vacant" and self._device.presence != "Unavailable"


class CrestronHomeDoorSensor(CrestronHomeBinarySensor):
    """Representation of a Crestron Home door sensor."""

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: CrestronDevice,
    ) -> None:
        """Initialize the door sensor."""
        super().__init__(coordinator, device)
        self._attr_device_class = BinarySensorDeviceClass.DOOR
    
    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on (door is open)."""
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_BINARY_SENSOR, []):
            if device.id == self._device.id:
                # "Closed" means door is closed, "Open" means door is open
                return device.door_status == "Open"
        
        # If device not found, use the stored state
        return self._device.door_status == "Open"
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attributes = {}
        
        # Add battery level if available
        battery_level = None
        
        # Find the device in the coordinator data
        for device in self.coordinator.data.get(DEVICE_TYPE_BINARY_SENSOR, []):
            if device.id == self._device.id:
                battery_level = device.battery_level
                break
        
        # If device not found, use the stored state
        if battery_level is None:
            battery_level = self._device.battery_level
        
        if battery_level:
            attributes["battery_level"] = battery_level
        
        return attributes

"""Diagnostics from cached Crestron device data."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_FIELDS = {
    "type",
    "subType",
    "status",
    "connectionStatus",
    "level",
    "position",
    "presence",
    "door_status",
    "battery_level",
    "currentTemperature",
    "temperatureUnits",
    "currentMode",
    "mode",
    "currentSetPoint",
    "setPoint",
    "availableSetPoints",
    "temperature",
    "minValue",
    "maxValue",
    "currentFanMode",
    "availableFanModes",
    "availableSystemModes",
    "schedulerState",
}


def _device_data(value: Any) -> Any:
    # Select known state fields so unexpected API fields cannot expose identifying data.
    if isinstance(value, dict):
        return {
            key: _device_data(item) for key, item in value.items() if key in _FIELDS
        }
    if isinstance(value, list):
        return [_device_data(item) for item in value]
    return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return device capabilities and state without configuration or identifiers."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is None:
        return {"loaded": False}

    return {
        "loaded": True,
        "last_update_success": coordinator.last_update_success,
        "update_interval": coordinator.update_interval.total_seconds(),
        "devices": [
            {
                "category": category,
                "available": device.is_available,
                "state_available": device.state_available,
                "hidden": device.ha_hidden,
                "data": _device_data(device.raw_data),
            }
            for category, devices in (coordinator.data or {}).items()
            for device in devices
        ],
    }

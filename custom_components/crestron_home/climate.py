"""Thermostats using the Crestron Home REST API."""

from __future__ import annotations

import math
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import CrestronApiError
from .const import DEVICE_TYPE_CLIMATE, DOMAIN, MANUFACTURER, MODEL
from .coordinator import CrestronHomeDataUpdateCoordinator
from .entity import CrestronRoomEntity
from .models import CrestronDevice

_UNITS = {
    "DeciCelsius": (UnitOfTemperature.CELSIUS, 10),
    "CelsiusWholeDegrees": (UnitOfTemperature.CELSIUS, 1),
    "DeciFahrenheit": (UnitOfTemperature.FAHRENHEIT, 10),
    "FahrenheitWholeDegrees": (UnitOfTemperature.FAHRENHEIT, 1),
}
_MODES = {
    "off": HVACMode.OFF,
    "heat": HVACMode.HEAT,
    "cool": HVACMode.COOL,
    "auto": HVACMode.HEAT_COOL,
}


def _number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CrestronHomeThermostat(coordinator, device)
        for device in coordinator.data.get(DEVICE_TYPE_CLIMATE, [])
    )


class CrestronHomeThermostat(CrestronRoomEntity, CoordinatorEntity, ClimateEntity):
    """A thermostat with capabilities reported by the processor."""

    _attr_has_entity_name = False
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        coordinator: CrestronHomeDataUpdateCoordinator,
        device: CrestronDevice,
    ) -> None:
        super().__init__(coordinator)
        self._device = self._device_info = device
        self._attr_unique_id = f"crestron_thermostat_{device.id}"
        self._attr_name = device.full_name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device.id))},
            name=device.full_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            via_device_id=coordinator.controller_device_id,
            suggested_area=device.room,
        )

    @property
    def _data(self) -> dict[str, Any]:
        return self._device.raw_data

    @property
    def _unit(self) -> tuple[str, int] | None:
        return _UNITS.get(self._data.get("temperatureUnits"))

    def _temperature(self, value: Any) -> float | None:
        if self._unit is None or not _number(value):
            return None
        return value / self._unit[1]

    @property
    def available(self) -> bool:
        return (
            self.coordinator.last_update_success
            and self._device.is_available
            and self._unit is not None
        )

    @property
    def temperature_unit(self) -> str:
        return self._unit[0] if self._unit else UnitOfTemperature.CELSIUS

    @property
    def target_temperature_step(self) -> float | None:
        return 1 / self._unit[1] if self._unit else None

    @property
    def current_temperature(self) -> float | None:
        return self._temperature(self._data.get("currentTemperature"))

    @property
    def hvac_mode(self) -> HVACMode | None:
        mode = self._data.get("currentMode") or self._data.get("mode")
        return _MODES.get(str(mode).lower())

    @property
    def hvac_modes(self) -> list[HVACMode]:
        return list(
            dict.fromkeys(
                _MODES[mode.lower()]
                for mode in (self._data.get("availableSystemModes") or [])
                if isinstance(mode, str) and mode.lower() in _MODES
            )
        )

    @property
    def _setpoints(self) -> dict[str, dict[str, Any]]:
        current = self._data.get("currentSetPoint") or self._data.get("setPoint") or []
        if isinstance(current, dict):
            current = [current]
        points = {}
        for point in [*(self._data.get("availableSetPoints") or []), *current]:
            kind = str(point.get("type", "")).lower()
            points.setdefault(kind, {}).update(point)
        return points

    @property
    def _targets(self) -> list[str]:
        points = self._setpoints
        if self.hvac_mode == HVACMode.HEAT_COOL:
            kinds = ["auto"] if "auto" in points else ["heat", "cool"]
        elif self.hvac_mode in (HVACMode.HEAT, HVACMode.COOL):
            kinds = [self.hvac_mode.value]
        else:
            return []
        if self._unit and all(
            kind in points
            and _number(points[kind].get("minValue"))
            and _number(points[kind].get("maxValue"))
            and points[kind]["minValue"] <= points[kind]["maxValue"]
            for kind in kinds
        ):
            return kinds
        return []

    @property
    def supported_features(self) -> ClimateEntityFeature:
        features = ClimateEntityFeature(0)
        if self.fan_modes:
            features |= ClimateEntityFeature.FAN_MODE
        if len(self._targets) == 1:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        elif len(self._targets) == 2:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        return features

    @property
    def target_temperature(self) -> float | None:
        if len(self._targets) == 1:
            return self._temperature(
                self._setpoints[self._targets[0]].get("temperature")
            )
        return None

    @property
    def target_temperature_low(self) -> float | None:
        if len(self._targets) == 2:
            return self._temperature(self._setpoints["heat"].get("temperature"))
        return None

    @property
    def target_temperature_high(self) -> float | None:
        if len(self._targets) == 2:
            return self._temperature(self._setpoints["cool"].get("temperature"))
        return None

    @property
    def min_temp(self) -> float:
        if self._targets:
            return self._temperature(
                min(self._setpoints[k]["minValue"] for k in self._targets)
            )
        return super().min_temp

    @property
    def max_temp(self) -> float:
        if self._targets:
            return self._temperature(
                max(self._setpoints[k]["maxValue"] for k in self._targets)
            )
        return super().max_temp

    @property
    def fan_mode(self) -> str | None:
        mode = self._data.get("currentFanMode")
        return mode.lower() if isinstance(mode, str) else None

    @property
    def fan_modes(self) -> list[str]:
        return [
            mode.lower()
            for mode in (self._data.get("availableFanModes") or [])
            if isinstance(mode, str)
        ]

    async def _command(self, action: str, value: Any) -> None:
        if not self.available:
            raise HomeAssistantError(
                "Thermostat is unavailable or its temperature unit is unsupported"
            )
        try:
            await self.coordinator.client.set_thermostat(self._device.id, action, value)
        except CrestronApiError as error:
            raise HomeAssistantError(str(error)) from error
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode not in self.hvac_modes:
            raise ServiceValidationError("Unsupported thermostat mode")
        mode = next(key for key, value in _MODES.items() if value == hvac_mode)
        await self._command("mode", mode.upper())

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        if fan_mode not in self.fan_modes:
            raise ServiceValidationError("Unsupported fan mode")
        await self._command("fanmode", fan_mode.upper())

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if kwargs.get("hvac_mode") not in (None, self.hvac_mode):
            raise ServiceValidationError(
                "Change the thermostat mode before setting its temperature"
            )
        targets = self._targets
        if not targets:
            raise ServiceValidationError(
                "No supported temperature target for the current mode"
            )
        if len(targets) == 1:
            values = {targets[0]: kwargs.get(ATTR_TEMPERATURE)}
        else:
            values = {
                "heat": kwargs.get("target_temp_low", self.target_temperature_low),
                "cool": kwargs.get("target_temp_high", self.target_temperature_high),
            }
            if ATTR_TEMPERATURE in kwargs:
                raise ServiceValidationError(
                    "Specify lower and upper temperatures for heat/cool mode"
                )
        payload = []
        for kind, value in values.items():
            point = self._setpoints[kind]
            if not _number(value):
                raise ServiceValidationError("A finite target temperature is required")
            raw = value * self._unit[1]
            if not point["minValue"] <= raw <= point["maxValue"]:
                raise ServiceValidationError(
                    "Target temperature is outside the thermostat limits"
                )
            payload.append({"type": kind.title(), "temperature": round(raw)})
        if len(targets) == 2 and payload[0]["temperature"] > payload[1]["temperature"]:
            raise ServiceValidationError(
                "The heating target must not exceed the cooling target"
            )
        await self._command("SetPoint", payload)

    @callback
    def _handle_coordinator_update(self) -> None:
        for device in self.coordinator.data.get(DEVICE_TYPE_CLIMATE, []):
            if device.id == self._device.id:
                self._device = self._device_info = device
                break
        self.async_write_ha_state()

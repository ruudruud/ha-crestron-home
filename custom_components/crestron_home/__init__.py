"""The Crestron Home integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import CrestronApiError, CrestronClient
from .const import (
    CONF_ENABLED_DEVICE_TYPES,
    CONF_HOST,
    CONF_TOKEN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_SCENE,
    DEVICE_TYPE_SHADE,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)
from .coordinator import CrestronHomeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Crestron Home from a config entry."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    host = entry.data.get(CONF_HOST)
    token = entry.data.get(CONF_TOKEN)
    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    enabled_device_types = entry.data.get(CONF_ENABLED_DEVICE_TYPES, [])

    # Create API client
    client = CrestronClient(hass, host, token)

    # Create coordinator
    coordinator = CrestronHomeDataUpdateCoordinator(
        hass, client, update_interval, enabled_device_types
    )

    # Fetch initial data
    try:
        await coordinator.async_config_entry_first_refresh()
    except CrestronApiError as err:
        raise ConfigEntryNotReady(f"Failed to connect to Crestron Home: {err}") from err

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up only enabled platforms
    enabled_device_types = entry.data.get(CONF_ENABLED_DEVICE_TYPES, [])
    enabled_platforms = []
    
    # Map device types to platforms
    if DEVICE_TYPE_LIGHT in enabled_device_types:
        enabled_platforms.append(Platform.LIGHT)
    if DEVICE_TYPE_SHADE in enabled_device_types:
        enabled_platforms.append(Platform.COVER)
    if DEVICE_TYPE_SCENE in enabled_device_types:
        enabled_platforms.append(Platform.SCENE)
    
    _LOGGER.debug("Setting up enabled platforms: %s", enabled_platforms)
    await hass.config_entries.async_forward_entry_setups(entry, enabled_platforms)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Get enabled platforms
    enabled_device_types = entry.data.get(CONF_ENABLED_DEVICE_TYPES, [])
    enabled_platforms = []
    
    # Map device types to platforms
    if DEVICE_TYPE_LIGHT in enabled_device_types:
        enabled_platforms.append(Platform.LIGHT)
    if DEVICE_TYPE_SHADE in enabled_device_types:
        enabled_platforms.append(Platform.COVER)
    if DEVICE_TYPE_SCENE in enabled_device_types:
        enabled_platforms.append(Platform.SCENE)
    
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, enabled_platforms):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

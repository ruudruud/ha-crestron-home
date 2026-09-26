"""The Crestron Home integration."""
from __future__ import annotations

import logging
from typing import List

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .api import CrestronApiError, CrestronClient
from .const import (
    CONF_ENABLED_DEVICE_TYPES,
    CONF_HOST,
    CONF_IGNORED_DEVICE_NAMES,
    CONF_TOKEN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_IGNORED_DEVICE_NAMES,
    DEFAULT_UPDATE_INTERVAL,
    DEVICE_TYPE_BINARY_SENSOR,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_SCENE,
    DEVICE_TYPE_SENSOR,
    DEVICE_TYPE_SHADE,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    STARTUP_MESSAGE,
)
from .coordinator import CrestronHomeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Crestron Home from a config entry."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    settings = {**entry.data, **entry.options}
    host = entry.data.get(CONF_HOST)
    token = entry.data.get(CONF_TOKEN)
    update_interval = settings.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    enabled_device_types = settings.get(CONF_ENABLED_DEVICE_TYPES, [])
    ignored_device_names = settings.get(CONF_IGNORED_DEVICE_NAMES, DEFAULT_IGNORED_DEVICE_NAMES)
    
    _LOGGER.debug("Ignored device name patterns: %s", ignored_device_names)

    # Create API client
    client = CrestronClient(hass, host, token)

    # Create coordinator with current configuration values
    _LOGGER.debug(
        "Creating coordinator with update_interval=%s, enabled_types=%s, ignored_names=%s",
        update_interval, enabled_device_types, ignored_device_names
    )
    
    coordinator = CrestronHomeDataUpdateCoordinator(
        hass, client, update_interval, enabled_device_types, ignored_device_names,
        config_entry=entry,
    )

    # Fetch initial data
    try:
        await coordinator.async_config_entry_first_refresh()
    except CrestronApiError as err:
        raise ConfigEntryNotReady(f"Failed to connect to Crestron Home: {err}") from err

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Register the Crestron Home controller as a device
    device_registry = async_get_device_registry(hass)
    controller = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, host)},
        name=f"Crestron Home ({host})",
        manufacturer=MANUFACTURER,
        model=MODEL,
    )

    coordinator.controller_device_id = controller.id

    await _async_clean_entity_registry(
        hass, entry,
        [kind for kind in (DEVICE_TYPE_LIGHT, DEVICE_TYPE_SHADE, DEVICE_TYPE_SCENE,
                          DEVICE_TYPE_BINARY_SENSOR, DEVICE_TYPE_SENSOR)
         if kind not in enabled_device_types],
    )

    # Set up only enabled platforms
    enabled_platforms = []
    
    # Map device types to platforms
    if DEVICE_TYPE_LIGHT in enabled_device_types:
        enabled_platforms.append(Platform.LIGHT)
    if DEVICE_TYPE_SHADE in enabled_device_types:
        enabled_platforms.append(Platform.COVER)
    if DEVICE_TYPE_SCENE in enabled_device_types:
        enabled_platforms.append(Platform.SCENE)
    if DEVICE_TYPE_BINARY_SENSOR in enabled_device_types:
        enabled_platforms.append(Platform.BINARY_SENSOR)
    if DEVICE_TYPE_SENSOR in enabled_device_types:
        enabled_platforms.append(Platform.SENSOR)
    
    _LOGGER.debug("Setting up enabled platforms: %s", enabled_platforms)
    await hass.config_entries.async_forward_entry_setups(entry, enabled_platforms)

    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Options already contain the new selection; unload the platforms actually running.
    coordinator = hass.data[DOMAIN][entry.entry_id]
    enabled_device_types = coordinator.enabled_device_types
    enabled_platforms = []
    
    # Map device types to platforms
    if DEVICE_TYPE_LIGHT in enabled_device_types:
        enabled_platforms.append(Platform.LIGHT)
    if DEVICE_TYPE_SHADE in enabled_device_types:
        enabled_platforms.append(Platform.COVER)
    if DEVICE_TYPE_SCENE in enabled_device_types:
        enabled_platforms.append(Platform.SCENE)
    if DEVICE_TYPE_BINARY_SENSOR in enabled_device_types:
        enabled_platforms.append(Platform.BINARY_SENSOR)
    if DEVICE_TYPE_SENSOR in enabled_device_types:
        enabled_platforms.append(Platform.SENSOR)
    
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, enabled_platforms):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _async_clean_entity_registry(
    hass: HomeAssistant, 
    entry: ConfigEntry,
    disabled_device_types: List[str]
) -> None:
    """Remove entities for disabled device types from the entity registry."""
    entity_registry = async_get_entity_registry(hass)
    
    # Map device types to platform domains
    domain_mapping = {
        DEVICE_TYPE_LIGHT: Platform.LIGHT,
        DEVICE_TYPE_SHADE: Platform.COVER,
        DEVICE_TYPE_SCENE: Platform.SCENE,
        DEVICE_TYPE_BINARY_SENSOR: Platform.BINARY_SENSOR,
        DEVICE_TYPE_SENSOR: Platform.SENSOR,
    }
    
    # Get domains to clean up
    domains_to_clean = [domain_mapping[device_type] for device_type in disabled_device_types 
                        if device_type in domain_mapping]
    
    _LOGGER.debug("Cleaning up entities for domains: %s", domains_to_clean)
    
    # Get entities to remove (those belonging to this config entry and disabled domains)
    entities_to_remove = [
        entity_id for entity_id, entity in entity_registry.entities.items()
        if entity.config_entry_id == entry.entry_id and entity.domain in domains_to_clean
    ]
    
    # Remove entities
    for entity_id in entities_to_remove:
        _LOGGER.debug("Removing entity %s from registry", entity_id)
        entity_registry.async_remove(entity_id)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Let Home Assistant manage the config entry lifecycle."""
    await hass.config_entries.async_reload(entry.entry_id)

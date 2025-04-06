"""Config flow for Crestron Home integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .api import CrestronApiError, CrestronAuthError, CrestronClient, CrestronConnectionError
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
    MIN_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    client = CrestronClient(
        hass=hass,
        host=data[CONF_HOST],
        token=data[CONF_TOKEN],
    )

    try:
        await client.login()
    except CrestronConnectionError as error:
        raise CannotConnect from error
    except CrestronAuthError as error:
        raise InvalidAuth from error
    except CrestronApiError as error:
        raise CannotConnect from error

    # Return info that you want to store in the config entry.
    return {"title": f"Crestron Home ({data[CONF_HOST]})"}


class CrestronHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Crestron Home."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CrestronHomeOptionsFlowHandler:
        """Get the options flow for this handler."""
        return CrestronHomeOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Set default enabled device types if not provided
                if CONF_ENABLED_DEVICE_TYPES not in user_input:
                    user_input[CONF_ENABLED_DEVICE_TYPES] = [
                        DEVICE_TYPE_LIGHT,
                        DEVICE_TYPE_SHADE,
                        DEVICE_TYPE_SCENE,
                        DEVICE_TYPE_BINARY_SENSOR,
                        DEVICE_TYPE_SENSOR,
                    ]
                
                return self.async_create_entry(title=info["title"], data=user_input)
            
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # If there are no user inputs or there were errors, show the form again
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_TOKEN): str,
                    vol.Required(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_UPDATE_INTERVAL,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="seconds",
                        ),
                    ),
                    vol.Optional(CONF_ENABLED_DEVICE_TYPES, default=[
                        DEVICE_TYPE_LIGHT,
                        DEVICE_TYPE_SHADE,
                        DEVICE_TYPE_SCENE,
                        DEVICE_TYPE_BINARY_SENSOR,
                        DEVICE_TYPE_SENSOR,
                    ]): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": DEVICE_TYPE_LIGHT, "label": "Lights"},
                                {"value": DEVICE_TYPE_SHADE, "label": "Shades"},
                                {"value": DEVICE_TYPE_SCENE, "label": "Scenes"},
                                {"value": DEVICE_TYPE_BINARY_SENSOR, "label": "Binary Sensors"},
                                {"value": DEVICE_TYPE_SENSOR, "label": "Sensors"},
                            ],
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        ),
                    ),
                    vol.Optional(CONF_IGNORED_DEVICE_NAMES, default=DEFAULT_IGNORED_DEVICE_NAMES): selector.TextSelector(
                        selector.TextSelectorConfig(
                            multiple=True,
                            suffix="Use % as wildcard (e.g., %bathroom%, bathroom%, %bathroom)",
                        ),
                    ),
                }
            ),
            errors=errors,
        )


class CrestronHomeOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Crestron Home options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Validate the updated configuration
            try:
                client = CrestronClient(
                    hass=self.hass,
                    host=self.config_entry.data[CONF_HOST],
                    token=self.config_entry.data[CONF_TOKEN],
                )
                await client.login()
                
                # Return the options to be stored in entry.options
                # The async_reload_entry function will handle merging these with the data
                return self.async_create_entry(title="", data=user_input)
            
            except CrestronConnectionError:
                errors["base"] = "cannot_connect"
            except CrestronAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Get current values from config entry
        current_update_interval = self.config_entry.data.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )
        current_enabled_types = self.config_entry.data.get(
            CONF_ENABLED_DEVICE_TYPES, [DEVICE_TYPE_LIGHT, DEVICE_TYPE_SHADE, DEVICE_TYPE_SCENE, DEVICE_TYPE_BINARY_SENSOR, DEVICE_TYPE_SENSOR]
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL, default=current_update_interval
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_UPDATE_INTERVAL,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="seconds",
                        ),
                    ),
                    vol.Required(
                        CONF_ENABLED_DEVICE_TYPES, default=current_enabled_types
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": DEVICE_TYPE_LIGHT, "label": "Lights"},
                                {"value": DEVICE_TYPE_SHADE, "label": "Shades"},
                                {"value": DEVICE_TYPE_SCENE, "label": "Scenes"},
                                {"value": DEVICE_TYPE_BINARY_SENSOR, "label": "Binary Sensors"},
                                {"value": DEVICE_TYPE_SENSOR, "label": "Sensors"},
                            ],
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        ),
                    ),
                    vol.Optional(
                        CONF_IGNORED_DEVICE_NAMES, 
                        default=self.config_entry.data.get(CONF_IGNORED_DEVICE_NAMES, DEFAULT_IGNORED_DEVICE_NAMES)
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            multiple=True,
                            suffix="Use % as wildcard (e.g., %bathroom%, bathroom%, %bathroom)",
                        ),
                    ),
                }
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

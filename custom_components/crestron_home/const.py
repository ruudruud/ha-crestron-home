"""Constants for the Crestron Home integration."""
from typing import Final

from homeassistant.const import (
    Platform,
)

# Base component constants
DOMAIN: Final = "crestron_home"
MANUFACTURER: Final = "Crestron"
MODEL: Final = "Crestron Home OS"
ATTRIBUTION: Final = "Data provided by Crestron Home® OS REST API"

# Platforms
PLATFORMS: Final = [Platform.LIGHT, Platform.COVER, Platform.SCENE, Platform.BINARY_SENSOR, Platform.SENSOR]

# Configuration and options
CONF_HOST: Final = "host"
CONF_TOKEN: Final = "token"
CONF_UPDATE_INTERVAL: Final = "update_interval"
CONF_ENABLED_DEVICE_TYPES: Final = "enabled_device_types"

# Defaults
DEFAULT_UPDATE_INTERVAL: Final = 15
MIN_UPDATE_INTERVAL: Final = 10

# Device types
DEVICE_TYPE_LIGHT: Final = "light"
DEVICE_TYPE_SHADE: Final = "shade"
DEVICE_TYPE_SCENE: Final = "scene"
DEVICE_TYPE_BINARY_SENSOR: Final = "binary_sensor"
DEVICE_TYPE_SENSOR: Final = "sensor"

# Device subtypes
DEVICE_SUBTYPE_DIMMER: Final = "Dimmer"
DEVICE_SUBTYPE_SWITCH: Final = "Switch"
DEVICE_SUBTYPE_SHADE: Final = "Shade"
DEVICE_SUBTYPE_SCENE: Final = "Scene"
DEVICE_SUBTYPE_OCCUPANCY_SENSOR: Final = "OccupancySensor"
DEVICE_SUBTYPE_PHOTO_SENSOR: Final = "PhotoSensor"
DEVICE_SUBTYPE_DOOR_SENSOR: Final = "DoorSensor"

# Crestron API constants
CRESTRON_API_PATH: Final = "/cws/api"
CRESTRON_SESSION_TIMEOUT: Final = 9 * 60  # 9 minutes (Crestron session TTL is 10 minutes)
CRESTRON_MAX_LEVEL: Final = 65535  # Maximum level value for Crestron devices

# Startup message
STARTUP_MESSAGE: Final = f"""
-------------------------------------------------------------------
{DOMAIN}
This is a custom integration for Crestron Home
-------------------------------------------------------------------
"""

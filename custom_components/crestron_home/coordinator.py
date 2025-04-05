"""DataUpdateCoordinator for Crestron Home integration."""
from datetime import timedelta
import logging
from typing import Any, Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import CrestronApiError, CrestronAuthError, CrestronClient, CrestronConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CrestronHomeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Crestron Home system."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: CrestronClient,
        update_interval: int,
        enabled_device_types: List[str],
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.enabled_device_types = enabled_device_types
        self.devices: List[Dict[str, Any]] = []
        self.platforms = []

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via API client."""
        try:
            _LOGGER.debug("Updating data with enabled device types: %s", self.enabled_device_types)
            
            # Get all devices from the Crestron Home system
            self.devices = await self.client.get_devices(self.enabled_device_types)
            _LOGGER.debug("Received %d devices from API", len(self.devices))
            
            # Organize devices by type for easier access
            devices_by_type = {
                "light": [],
                "shade": [],
                "scene": [],
            }
            
            for device in self.devices:
                # Use the mapped Home Assistant device type
                ha_device_type = device.get("ha_device_type")
                
                if ha_device_type and ha_device_type in devices_by_type:
                    devices_by_type[ha_device_type].append(device)
                    _LOGGER.debug("Added device to %s platform: %s", ha_device_type, device.get("name"))
            
            # Log device counts by type
            for device_type, type_devices in devices_by_type.items():
                _LOGGER.info("Found %d devices for %s platform", len(type_devices), device_type)
            
            return devices_by_type
        
        except CrestronConnectionError as error:
            raise UpdateFailed(f"Connection error: {error}")
        
        except CrestronAuthError as error:
            raise UpdateFailed(f"Authentication error: {error}")
        
        except CrestronApiError as error:
            raise UpdateFailed(f"API error: {error}")
        
        except Exception as error:
            raise UpdateFailed(f"Unexpected error: {error}")

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
            # Get all devices from the Crestron Home system
            self.devices = await self.client.get_devices(self.enabled_device_types)
            
            # Organize devices by type for easier access
            devices_by_type = {
                "light": [],
                "shade": [],
                "scene": [],
            }
            
            for device in self.devices:
                device_type = device.get("type", "").lower()
                
                # Map Crestron device types to Home Assistant platform types
                if device_type == "dimmer" or device_type == "switch":
                    devices_by_type["light"].append(device)
                elif device_type == "shade":
                    devices_by_type["shade"].append(device)
                elif device_type == "scene":
                    devices_by_type["scene"].append(device)
            
            return devices_by_type
        
        except CrestronConnectionError as error:
            raise UpdateFailed(f"Connection error: {error}")
        
        except CrestronAuthError as error:
            raise UpdateFailed(f"Authentication error: {error}")
        
        except CrestronApiError as error:
            raise UpdateFailed(f"API error: {error}")
        
        except Exception as error:
            raise UpdateFailed(f"Unexpected error: {error}")

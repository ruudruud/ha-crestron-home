"""Data models for Crestron Home integration."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class CrestronDevice:
    """Representation of a Crestron device."""

    id: int
    room: str
    name: str
    type: str
    subtype: str
    status: bool = False
    level: int = 0
    connection: str = "online"
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Home Assistant specific fields
    ha_state: bool = True
    ha_hidden: bool = False
    ha_reason: str = ""
    
    # Room information
    room_id: Optional[int] = None
    
    # Additional fields for specific device types
    position: int = 0  # For shades/covers
    value: Any = None  # For sensors
    unit: str = ""     # For sensors
    battery_level: str = ""  # For door sensors
    presence: str = ""  # For occupancy sensors
    door_status: str = ""  # For door sensors
    
    # Raw data from API
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        """Return the full name of the device including room."""
        return f"{self.room} {self.name}".strip()
    
    @property
    def is_available(self) -> bool:
        """Return if the device is available."""
        return self.connection != "offline"

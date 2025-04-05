#!/usr/bin/env python3
"""Test script for the Crestron Home client.

This script can be used to test the connection to a Crestron Home system
and verify that the client can retrieve devices and control them.

Usage:
  python test_client.py [options]

Options:
  --host HOST         Hostname or IP address of the Crestron Home system (overrides .env)
  --token TOKEN       Authentication token for the Crestron Home system (overrides .env)
  --room ROOM         Filter lights by room name
  --sort {name,room,status,level}
                      Sort lights by the specified field (default: room)
  --all               Show all devices, not just lights
  --raw               Show raw API data instead of formatted output
  --help              Show this help message and exit

Examples:
  python test_client.py --room "Living Room" --sort level
  python test_client.py --room "Bijkeuken" --raw
"""

import argparse
import asyncio
import os
import ssl
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from dotenv import load_dotenv


class CrestronApiError(Exception):
    """Exception to indicate a general API error."""


class CrestronAuthError(CrestronApiError):
    """Exception to indicate an authentication error."""


class CrestronConnectionError(CrestronApiError):
    """Exception to indicate a connection error."""


# ANSI color codes for terminal output
ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_BLUE = "\033[94m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"


class CrestronClient:
    """API Client for Crestron Home."""

    # Constants for Crestron level conversion
    MAX_LEVEL = 65535

    def __init__(self, host: str, token: str) -> None:
        """Initialize the API client."""
        self.host = host
        self.api_token = token
        self.base_url = f"https://{host}/cws/api"
        self.auth_key: Optional[str] = None
        self.last_login: float = 0
        self.rooms: List[Dict[str, Any]] = []
        self._session: Optional[aiohttp.ClientSession] = None

    async def login(self) -> None:
        """Login to the Crestron Home system."""
        # Check if we need to login (session expires after 10 minutes)
        current_time = time.time()
        if self.auth_key and (current_time - self.last_login) < 9 * 60:  # 9 minutes
            print("Session is still valid, skipping login")
            return

        print(f"Logging in to Crestron Home at {self.base_url}")
        
        try:
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Make login request
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                headers = {
                    "Accept": "application/json",
                    "Crestron-RestAPI-AuthToken": self.api_token,
                }
                
                async with session.get(
                    f"{self.base_url}/login",
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    self.auth_key = data.get("authkey")
                    if not self.auth_key:
                        raise CrestronAuthError("No authentication key received")
                    
                    self.last_login = current_time
                    print(
                        f"Successfully authenticated with Crestron Home, version: {data.get('version', 'unknown')}"
                    )
                    
                    # Create a new session with the auth key
                    self._session = aiohttp.ClientSession(
                        connector=aiohttp.TCPConnector(ssl=ssl_context),
                        headers={"Crestron-RestAPI-AuthKey": self.auth_key}
                    )
        
        except aiohttp.ClientConnectorError as error:
            print(f"Connection error: {error}")
            raise CrestronConnectionError(f"Connection error: {error}") from error
        
        except aiohttp.ClientResponseError as error:
            print(f"Authentication error: {error}")
            raise CrestronAuthError(f"Authentication error: {error}") from error
        
        except Exception as error:
            print(f"Unexpected error during login: {error}")
            raise CrestronApiError(f"Unexpected error: {error}") from error

    async def _api_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an API request to the Crestron Home system."""
        await self.login()
        
        if not self.auth_key or not self._session:
            raise CrestronAuthError("Not authenticated")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self._session.request(
                method, url, json=data
            ) as response:
                response.raise_for_status()
                return await response.json()
        
        except aiohttp.ClientResponseError as error:
            if error.status == 401:
                # Force re-authentication on next request
                self.auth_key = None
                self.last_login = 0
                if self._session:
                    await self._session.close()
                    self._session = None
                raise CrestronAuthError("Authentication expired") from error
            raise CrestronApiError(f"API error: {error}") from error
        
        except Exception as error:
            print(f"API request error: {error}")
            raise CrestronApiError(f"API request error: {error}") from error

    @staticmethod
    def crestron_to_percentage(value: int) -> int:
        """Convert a Crestron range value (0-65535) to percentage (0-100)."""
        if value <= 0:
            return 0
        return round((value / CrestronClient.MAX_LEVEL) * 100)

    @staticmethod
    def percentage_to_crestron(value: int) -> int:
        """Convert a percentage (0-100) to Crestron range value (0-65535)."""
        if value <= 0:
            return 0
        return round((CrestronClient.MAX_LEVEL * value) / 100)

    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices from the Crestron Home system."""
        print("Getting devices from Crestron Home...")
        
        try:
            # Get rooms, scenes, devices, shades, and sensors in parallel
            results = await asyncio.gather(
                self._api_request("GET", "/rooms"),
                self._api_request("GET", "/scenes"),
                self._api_request("GET", "/devices"),
                self._api_request("GET", "/shades"),
                self._api_request("GET", "/sensors"),
            )
            
            rooms_data = results[0]
            scenes_data = results[1]
            devices_data = results[2]
            shades_data = results[3]
            sensors_data = results[4]
            
            # Store rooms for later use
            self.rooms = rooms_data.get("rooms", [])
            
            devices: List[Dict[str, Any]] = []
            
            # Process regular devices
            for device in devices_data.get("devices", []):
                room_name = next(
                    (r.get("name", "") for r in self.rooms if r.get("id") == device.get("roomId")),
                    "",
                )
                
                device_type = device.get("subType") or device.get("type", "")
                shade_position = 0
                
                if device_type == "Shade":
                    # Find matching shade position
                    for shade in shades_data.get("shades", []):
                        if shade.get("id") == device.get("id"):
                            shade_position = shade.get("position", 0)
                            break
                
                device_info = {
                    "id": device.get("id"),
                    "type": device_type,
                    "subType": device_type,
                    "name": f"{room_name} {device.get('name', '')}",
                    "roomId": device.get("roomId"),
                    "roomName": room_name,
                    "level": device.get("level", 0),
                    "status": device.get("status", False),
                    "position": shade_position,
                    "connectionStatus": device.get("connectionStatus", "unknown"),
                }
                
                devices.append(device_info)
            
            # Process scenes
            for scene in scenes_data.get("scenes", []):
                room_name = next(
                    (r.get("name", "") for r in self.rooms if r.get("id") == scene.get("roomId")),
                    "",
                )
                
                scene_info = {
                    "id": scene.get("id"),
                    "type": "Scene",
                    "subType": scene.get("type", ""),
                    "name": f"{room_name} {scene.get('name', '')}",
                    "roomId": scene.get("roomId"),
                    "roomName": room_name,
                    "level": 0,
                    "status": scene.get("status", False),
                    "position": 0,
                    "connectionStatus": "n/a",  # Scenes don't have connection status
                }
                
                devices.append(scene_info)
            
            return devices
        
        except Exception as error:
            print(f"Error getting devices: {error}")
            return []

    async def close(self) -> None:
        """Close the client session."""
        if self._session:
            await self._session.close()


def load_config() -> Tuple[str, str, List[str]]:
    """Load configuration from .env file or environment variables."""
    # Load .env file if it exists
    load_dotenv()
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "")
    token = os.getenv("TOKEN", "")
    enabled_device_types = os.getenv("ENABLED_DEVICE_TYPES", "light,shade,scene").split(",")
    
    return host, token, enabled_device_types


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test script for the Crestron Home client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--host", 
        help="Hostname or IP address of the Crestron Home system (overrides .env)"
    )
    parser.add_argument(
        "--token", 
        help="Authentication token for the Crestron Home system (overrides .env)"
    )
    parser.add_argument(
        "--room", 
        help="Filter lights by room name"
    )
    parser.add_argument(
        "--sort", 
        choices=["name", "room", "status", "level"],
        default="room",
        help="Sort lights by the specified field (default: room)"
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Show all devices, not just lights"
    )
    parser.add_argument(
        "--raw", 
        action="store_true",
        help="Show raw API data instead of formatted output"
    )
    
    return parser.parse_args()


def print_light_table(lights: List[Dict[str, Any]], sort_by: str = "room") -> None:
    """Print a formatted table of lights."""
    if not lights:
        print("No lights found.")
        return
    
    # Sort lights based on the specified field
    if sort_by == "name":
        lights.sort(key=lambda x: x["name"])
    elif sort_by == "room":
        lights.sort(key=lambda x: (x["roomName"], x["name"]))
    elif sort_by == "status":
        lights.sort(key=lambda x: (not x["level"] > 0, x["roomName"], x["name"]))
    elif sort_by == "level":
        lights.sort(key=lambda x: (x["level"], x["roomName"], x["name"]), reverse=True)
    
    # Calculate column widths
    id_width = max(len("ID"), max(len(str(light["id"])) for light in lights))
    room_width = max(len("Room"), max(len(light["roomName"]) for light in lights))
    name_width = max(len("Name"), max(len(light["name"].replace(light["roomName"], "").strip()) for light in lights))
    type_width = max(len("Type"), max(len(light["type"]) for light in lights))
    conn_width = max(len("Connection"), max(len(light["connectionStatus"]) for light in lights))
    
    # Print header
    header = (
        f"{ANSI_BOLD}{'ID':<{id_width}} | "
        f"{'Room':<{room_width}} | "
        f"{'Name':<{name_width}} | "
        f"{'Type':<{type_width}} | "
        f"{'Status':<8} | "
        f"{'Level':<10} | "
        f"{'Connection':<{conn_width}}{ANSI_RESET}"
    )
    print("\n" + header)
    print("-" * len(header.replace(ANSI_BOLD, "").replace(ANSI_RESET, "")))
    
    # Print each light
    current_room = ""
    for light in lights:
        # Extract the name without the room name prefix
        name = light["name"].replace(light["roomName"], "").strip()
        
        # Add a separator between rooms
        if sort_by == "room" and light["roomName"] != current_room:
            if current_room:  # Not the first room
                print("-" * len(header.replace(ANSI_BOLD, "").replace(ANSI_RESET, "")))
            current_room = light["roomName"]
        
        # Determine status color
        status_color = ANSI_GREEN if light["level"] > 0 else ANSI_RED
        status_text = f"{status_color}{'ON' if light['level'] > 0 else 'OFF'}{ANSI_RESET}"
        
        # Calculate brightness percentage
        level_percent = CrestronClient.crestron_to_percentage(light["level"])
        level_text = f"{level_percent}%" if light["type"] == "Dimmer" else "N/A"
        
        # Determine connection status color
        conn_status = light["connectionStatus"]
        if conn_status == "online":
            conn_text = f"{ANSI_GREEN}{conn_status}{ANSI_RESET}"
        elif conn_status == "offline":
            conn_text = f"{ANSI_RED}{conn_status}{ANSI_RESET}"
        else:
            conn_text = conn_status
        
        # Print the light information
        print(
            f"{light['id']:<{id_width}} | "
            f"{ANSI_BLUE}{light['roomName']:<{room_width}}{ANSI_RESET} | "
            f"{name:<{name_width}} | "
            f"{light['type']:<{type_width}} | "
            f"{status_text:<8} | "
            f"{level_text:<10} | "
            f"{conn_text:<{conn_width + len(ANSI_GREEN) + len(ANSI_RESET) if conn_status in ['online', 'offline'] else conn_width}}"
        )


async def get_raw_api_data(client: CrestronClient) -> Dict[str, Any]:
    """Get raw API data from the Crestron Home system."""
    # Get rooms, scenes, devices, shades, and sensors in parallel
    results = await asyncio.gather(
        client._api_request("GET", "/rooms"),
        client._api_request("GET", "/scenes"),
        client._api_request("GET", "/devices"),
        client._api_request("GET", "/shades"),
        client._api_request("GET", "/sensors"),
    )
    
    return {
        "rooms": results[0],
        "scenes": results[1],
        "devices": results[2],
        "shades": results[3],
        "sensors": results[4],
    }

def print_raw_data_for_room(raw_data: Dict[str, Any], room_name: str) -> None:
    """Print raw API data for a specific room."""
    import json
    
    # Find the room ID for the specified room
    room_id = None
    room_data = None
    
    for room in raw_data["rooms"].get("rooms", []):
        if room_name.lower() in room.get("name", "").lower():
            room_id = room.get("id")
            room_data = room
            break
    
    if not room_id:
        print(f"Room '{room_name}' not found.")
        return
    
    # Print the raw room data
    print(f"\n{ANSI_BOLD}Raw Room Data:{ANSI_RESET}")
    print(json.dumps(room_data, indent=2))
    
    # Find devices in this room
    room_devices = []
    for device in raw_data["devices"].get("devices", []):
        if device.get("roomId") == room_id:
            room_devices.append(device)
    
    # Find scenes in this room
    room_scenes = []
    for scene in raw_data["scenes"].get("scenes", []):
        if scene.get("roomId") == room_id:
            room_scenes.append(scene)
    
    # Find shades in this room
    room_shades = []
    for shade in raw_data["shades"].get("shades", []):
        if shade.get("roomId") == room_id:
            room_shades.append(shade)
    
    # Find sensors in this room
    room_sensors = []
    for sensor in raw_data["sensors"].get("sensors", []):
        if sensor.get("roomId") == room_id:
            room_sensors.append(sensor)
    
    # Print the raw device data
    if room_devices:
        print(f"\n{ANSI_BOLD}Raw Device Data ({len(room_devices)} devices):{ANSI_RESET}")
        print(json.dumps(room_devices, indent=2))
    
    # Print the raw scene data
    if room_scenes:
        print(f"\n{ANSI_BOLD}Raw Scene Data ({len(room_scenes)} scenes):{ANSI_RESET}")
        print(json.dumps(room_scenes, indent=2))
    
    # Print the raw shade data
    if room_shades:
        print(f"\n{ANSI_BOLD}Raw Shade Data ({len(room_shades)} shades):{ANSI_RESET}")
        print(json.dumps(room_shades, indent=2))
    
    # Print the raw sensor data
    if room_sensors:
        print(f"\n{ANSI_BOLD}Raw Sensor Data ({len(room_sensors)} sensors):{ANSI_RESET}")
        print(json.dumps(room_sensors, indent=2))

async def main() -> None:
    """Run the test script."""
    # Load configuration from .env
    env_host, env_token, enabled_device_types = load_config()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Use command line arguments if provided, otherwise use .env values
    host = args.host or env_host
    token = args.token or env_token
    
    # Check if we have the required configuration
    if not host or not token:
        print("Error: Host and token are required. Provide them via .env file or command line arguments.")
        print(f"Usage: {sys.argv[0]} --host HOST --token TOKEN")
        sys.exit(1)
    
    client = CrestronClient(host, token)
    
    try:
        # Login to the Crestron Home system
        await client.login()
        print("Login successful!")
        
        if args.raw and args.room:
            # Get raw API data for the specified room
            raw_data = await get_raw_api_data(client)
            print_raw_data_for_room(raw_data, args.room)
        else:
            # Get all devices
            devices = await client.get_devices()
            print(f"Found {len(devices)} devices")
            
            # Filter devices based on command line arguments
            if args.all:
                filtered_devices = devices
            else:
                # Filter to only show lights (Dimmer and Switch types)
                filtered_devices = [
                    device for device in devices 
                    if device["type"] in ["Dimmer", "Switch"]
                ]
            
            # Apply room filter if specified
            if args.room:
                filtered_devices = [
                    device for device in filtered_devices 
                    if args.room.lower() in device["roomName"].lower()
                ]
            
            # Group devices by type for summary
            devices_by_type = {}
            for device in devices:
                device_type = device["type"]
                if device_type not in devices_by_type:
                    devices_by_type[device_type] = []
                devices_by_type[device_type].append(device)
            
            # Print device counts by type
            print("\nDevice summary:")
            for device_type, type_devices in sorted(devices_by_type.items()):
                print(f"  - {device_type}: {len(type_devices)}")
            
            # Print the light table
            if args.all:
                print(f"\nShowing all {len(filtered_devices)} devices:")
            else:
                print(f"\nShowing {len(filtered_devices)} lights:")
                if args.room:
                    print(f"(Filtered by room: {args.room})")
            
            print_light_table(filtered_devices, args.sort)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

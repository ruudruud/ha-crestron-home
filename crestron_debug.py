#!/usr/bin/env python3
"""Debugging tool for the Crestron Home system.

This script provides a command-line interface for testing and debugging
connections to a Crestron Home system. It allows you to:
- Verify connectivity to your Crestron Home system
- List and filter devices by type and room
- View device status and properties
- Examine raw API responses for troubleshooting

This tool is particularly useful for:
1. Debugging connection issues with your Crestron Home system
2. Verifying device discovery and configuration
3. Understanding the data structure of the Crestron Home API
4. Testing changes to the Home Assistant integration

Usage:
  python crestron_debug.py [options]

Options:
  --host HOST         Hostname or IP address of the Crestron Home system (overrides .env)
  --token TOKEN       Authentication token for the Crestron Home system (overrides .env)
  --room ROOM         Filter devices by room name
  --sort {name,room,status,level}
                      Sort devices by the specified field (default: room)
  --all               Show all devices, not just lights
  --sensors           Show only sensors (occupancy, door, photo)
  --raw               Show raw API data instead of formatted output
  --help              Show this help message and exit

Examples:
  python crestron_debug.py --room "Living Room" --sort level
  python crestron_debug.py --room "Bijkeuken" --raw
  python crestron_debug.py --sensors --room "Living Room"
  python crestron_debug.py --all --sort status
"""

import argparse
import asyncio
import json
import os
import ssl
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

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
    """API Client for Crestron Home.
    
    This class handles communication with the Crestron Home API, including:
    - Authentication
    - API requests
    - Data conversion
    - Device information retrieval
    
    Attributes:
        host: Hostname or IP address of the Crestron Home system
        api_token: Authentication token for the Crestron Home API
        base_url: Base URL for API requests
        auth_key: Current authentication key (obtained after login)
        last_login: Timestamp of the last successful login
        rooms: List of rooms retrieved from the API
    """

    # Constants for Crestron level conversion
    MAX_LEVEL = 65535

    def __init__(self, host: str, token: str) -> None:
        """Initialize the API client.
        
        Args:
            host: Hostname or IP address of the Crestron Home system
            token: Authentication token for the Crestron Home API
        """
        self.host = host
        self.api_token = token
        self.base_url = f"https://{host}/cws/api"
        self.auth_key: Optional[str] = None
        self.last_login: float = 0
        self.rooms: List[Dict[str, Any]] = []
        self._session: Optional[aiohttp.ClientSession] = None

    async def login(self) -> None:
        """Login to the Crestron Home system.
        
        This method authenticates with the Crestron Home API and obtains
        an authentication key for subsequent requests. It handles SSL
        certificate verification and session management.
        
        Raises:
            CrestronConnectionError: If connection to the Crestron Home system fails
            CrestronAuthError: If authentication fails
            CrestronApiError: For other API-related errors
        """
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
        """Make an API request to the Crestron Home system.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/devices")
            data: Optional JSON data to send with the request
            
        Returns:
            Dict containing the JSON response from the API
            
        Raises:
            CrestronAuthError: If authentication fails or expires
            CrestronApiError: For other API-related errors
        """
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
        """Convert a Crestron range value (0-65535) to percentage (0-100).
        
        Args:
            value: Crestron level value (0-65535)
            
        Returns:
            Percentage value (0-100)
        """
        if value <= 0:
            return 0
        return round((value / CrestronClient.MAX_LEVEL) * 100)

    @staticmethod
    def percentage_to_crestron(value: int) -> int:
        """Convert a percentage (0-100) to Crestron range value (0-65535).
        
        Args:
            value: Percentage value (0-100)
            
        Returns:
            Crestron level value (0-65535)
        """
        if value <= 0:
            return 0
        return round((CrestronClient.MAX_LEVEL * value) / 100)

    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices from the Crestron Home system.
        
        This method retrieves information about all devices, scenes, and shades
        from the Crestron Home system and normalizes the data into a consistent
        format.
        
        Returns:
            List of device dictionaries with normalized properties
        """
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
    """Load configuration from .env file or environment variables.
    
    Returns:
        Tuple containing:
        - host: Hostname or IP address of the Crestron Home system
        - token: Authentication token for the Crestron Home API
        - enabled_device_types: List of enabled device types
    """
    # Load .env file if it exists
    load_dotenv()
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "")
    token = os.getenv("TOKEN", "")
    enabled_device_types = os.getenv("ENABLED_DEVICE_TYPES", "light,shade,scene").split(",")
    
    return host, token, enabled_device_types


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Namespace containing the parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Debugging tool for the Crestron Home system",
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
        help="Filter devices by room name"
    )
    parser.add_argument(
        "--sort", 
        choices=["name", "room", "status", "level"],
        default="room",
        help="Sort devices by the specified field (default: room)"
    )
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Show all devices, not just lights"
    )
    parser.add_argument(
        "--sensors", 
        action="store_true",
        help="Show only sensors (occupancy, door, photo)"
    )
    parser.add_argument(
        "--raw", 
        action="store_true",
        help="Show raw API data instead of formatted output"
    )
    
    return parser.parse_args()


def print_light_table(devices: List[Dict[str, Any]], sort_by: str = "room") -> None:
    """Print a formatted table of devices.
    
    Args:
        devices: List of device dictionaries
        sort_by: Field to sort by (name, room, status, or level)
    """
    if not devices:
        print("No devices found.")
        return
    
    # Sort devices based on the specified field
    if sort_by == "name":
        devices.sort(key=lambda x: x["name"])
    elif sort_by == "room":
        devices.sort(key=lambda x: (x["roomName"], x["name"]))
    elif sort_by == "status":
        devices.sort(key=lambda x: (not x["level"] > 0, x["roomName"], x["name"]))
    elif sort_by == "level":
        devices.sort(key=lambda x: (x["level"], x["roomName"], x["name"]), reverse=True)
    
    # Calculate column widths
    id_width = max(len("ID"), max(len(str(device["id"])) for device in devices))
    room_width = max(len("Room"), max(len(device["roomName"]) for device in devices))
    name_width = max(len("Name"), max(len(device["name"].replace(device["roomName"], "").strip()) for device in devices))
    type_width = max(len("Type"), max(len(device["type"]) for device in devices))
    conn_width = max(len("Connection"), max(len(device["connectionStatus"]) for device in devices))
    
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
    
    # Print each device
    current_room = ""
    for device in devices:
        # Extract the name without the room name prefix
        name = device["name"].replace(device["roomName"], "").strip()
        
        # Add a separator between rooms
        if sort_by == "room" and device["roomName"] != current_room:
            if current_room:  # Not the first room
                print("-" * len(header.replace(ANSI_BOLD, "").replace(ANSI_RESET, "")))
            current_room = device["roomName"]
        
        # Determine status color
        status_color = ANSI_GREEN if device["level"] > 0 else ANSI_RED
        status_text = f"{status_color}{'ON' if device['level'] > 0 else 'OFF'}{ANSI_RESET}"
        
        # Calculate brightness percentage
        level_percent = CrestronClient.crestron_to_percentage(device["level"])
        level_text = f"{level_percent}%" if device["type"] == "Dimmer" else "N/A"
        
        # Determine connection status color
        conn_status = device["connectionStatus"]
        if conn_status == "online":
            conn_text = f"{ANSI_GREEN}{conn_status}{ANSI_RESET}"
        elif conn_status == "offline":
            conn_text = f"{ANSI_RED}{conn_status}{ANSI_RESET}"
        else:
            conn_text = conn_status
        
        # Print the device information
        print(
            f"{device['id']:<{id_width}} | "
            f"{ANSI_BLUE}{device['roomName']:<{room_width}}{ANSI_RESET} | "
            f"{name:<{name_width}} | "
            f"{device['type']:<{type_width}} | "
            f"{status_text:<8} | "
            f"{level_text:<10} | "
            f"{conn_text:<{conn_width + len(ANSI_GREEN) + len(ANSI_RESET) if conn_status in ['online', 'offline'] else conn_width}}"
        )


async def get_raw_api_data(client: CrestronClient) -> Dict[str, Any]:
    """Get raw API data from the Crestron Home system.
    
    Args:
        client: Initialized CrestronClient instance
        
    Returns:
        Dictionary containing raw API responses for rooms, scenes, devices, shades, and sensors
    """
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
    """Print raw API data for a specific room.
    
    Args:
        raw_data: Dictionary containing raw API responses
        room_name: Name of the room to filter by
    """
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


async def process_sensors(client: CrestronClient) -> List[Dict[str, Any]]:
    """Process sensors from the Crestron Home system.
    
    Args:
        client: Initialized CrestronClient instance
        
    Returns:
        List of processed sensor dictionaries
    """
    # Get sensors directly from the API
    sensors_data = await client._api_request("GET", "/sensors")
    sensors = sensors_data.get("sensors", [])
    
    # Process sensors to match device format
    processed_sensors = []
    for sensor in sensors:
        room_name = next(
            (r.get("name", "") for r in client.rooms if r.get("id") == sensor.get("roomId")),
            "",
        )
        
        sensor_type = sensor.get("subType", "")
        
        # Create sensor info with common fields
        sensor_info = {
            "id": sensor.get("id"),
            "type": sensor_type,
            "subType": sensor_type,
            "name": f"{room_name} {sensor.get('name', '')}".strip(),
            "roomId": sensor.get("roomId"),
            "roomName": room_name,
            "level": 0,  # Default for compatibility with table display
            "connectionStatus": sensor.get("connectionStatus", "unknown"),
        }
        
        # Add sensor-specific properties
        if sensor_type == "OccupancySensor":
            presence = sensor.get("presence", "Unavailable")
            sensor_info["presence"] = presence
            # Set level for table display (ON/OFF status)
            sensor_info["level"] = 65535 if (presence != "Vacant" and presence != "Unavailable") else 0
        elif sensor_type == "DoorSensor":
            sensor_info["door_status"] = sensor.get("door_status", "Closed")
            sensor_info["battery_level"] = sensor.get("battery_level", "Normal")
            # Set level for table display (ON/OFF status)
            sensor_info["level"] = 65535 if sensor.get("door_status") == "Open" else 0
        elif sensor_type == "PhotoSensor":
            sensor_info["level"] = sensor.get("level", 0)
        
        processed_sensors.append(sensor_info)
    
    return processed_sensors


async def main() -> None:
    """Run the debugging tool."""
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
        print("Create a .env file with the following content:")
        print("HOST=your-crestron-home-ip")
        print("TOKEN=your-crestron-home-token")
        print(f"Or use: {sys.argv[0]} --host HOST --token TOKEN")
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
            
            # Get sensors directly if requested
            if args.sensors:
                filtered_devices = await process_sensors(client)
                print(f"Found {len(filtered_devices)} sensors")
            # Filter devices based on command line arguments
            elif args.all:
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
            
            # Print the device table
            if args.sensors:
                print(f"\nShowing {len(filtered_devices)} sensors:")
                if args.room:
                    print(f"(Filtered by room: {args.room})")
            elif args.all:
                print(f"\nShowing all {len(filtered_devices)} devices:")
                if args.room:
                    print(f"(Filtered by room: {args.room})")
            else:
                print(f"\nShowing {len(filtered_devices)} lights:")
                if args.room:
                    print(f"(Filtered by room: {args.room})")
            
            print_light_table(filtered_devices, args.sort)
        
    except CrestronAuthError as e:
        print(f"Authentication error: {e}")
        print("Please check your authentication token and try again.")
        sys.exit(1)
    except CrestronConnectionError as e:
        print(f"Connection error: {e}")
        print("Please check your network connection and Crestron Home IP address.")
        sys.exit(1)
    except CrestronApiError as e:
        print(f"API error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

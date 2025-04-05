#!/usr/bin/env python3
"""Test script for the Crestron Home client.

This script can be used to test the connection to a Crestron Home system
and verify that the client can retrieve devices and control them.

Usage:
  python test_client.py <host> <token>

Example:
  python test_client.py 192.168.1.100 abcdef1234567890
"""

import asyncio
import logging
import ssl
import sys
import time
from typing import Any, Dict, List, Optional

import aiohttp


class CrestronApiError(Exception):
    """Exception to indicate a general API error."""


class CrestronAuthError(CrestronApiError):
    """Exception to indicate an authentication error."""


class CrestronConnectionError(CrestronApiError):
    """Exception to indicate a connection error."""


class CrestronClient:
    """API Client for Crestron Home."""

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

    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices from the Crestron Home system."""
        print("Getting devices from Crestron Home")
        
        try:
            # Get rooms, scenes, devices, and shades in parallel
            results = await asyncio.gather(
                self._api_request("GET", "/rooms"),
                self._api_request("GET", "/scenes"),
                self._api_request("GET", "/devices"),
                self._api_request("GET", "/shades"),
            )
            
            rooms_data = results[0]
            scenes_data = results[1]
            devices_data = results[2]
            shades_data = results[3]
            
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


async def main() -> None:
    """Run the test script."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <host> <token>")
        sys.exit(1)
    
    host = sys.argv[1]
    token = sys.argv[2]
    
    client = CrestronClient(host, token)
    
    try:
        # Test login
        await client.login()
        print("Login successful!")
        
        # Test getting devices
        devices = await client.get_devices()
        print(f"Found {len(devices)} devices:")
        
        # Group devices by type
        devices_by_type = {}
        for device in devices:
            device_type = device["type"]
            if device_type not in devices_by_type:
                devices_by_type[device_type] = []
            devices_by_type[device_type].append(device)
        
        # Print device counts by type
        for device_type, type_devices in devices_by_type.items():
            print(f"  - {device_type}: {len(type_devices)}")
        
        # Print some example devices
        print("\nExample devices:")
        for device_type, type_devices in devices_by_type.items():
            if type_devices:
                print(f"  {device_type}: {type_devices[0]['name']} (ID: {type_devices[0]['id']})")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

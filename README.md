# Home Assistant Integration for Crestron Home

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/ruudruud/ha-crestron-home.svg)](https://github.com/ruudruud/ha-crestron-home/releases)
[![GitHub License](https://img.shields.io/github/license/ruudruud/ha-crestron-home.svg)](LICENSE)

This repository contains a custom component for Home Assistant that integrates with Crestron Home systems. It allows you to control your Crestron Home devices (lights, shades, scenes) and monitor sensors through Home Assistant.

## Overview

The integration communicates with the Crestron Home CWS (Crestron Web Service) server via HTTP to discover and control devices in your Crestron Home system.

## Features

- **Lights**: Control Crestron Home lights (dimmers with brightness control, switches with on/off)
- **Shades**: Control Crestron Home shades (open, close, set position, stop movement)
- **Scenes**: Activate Crestron Home scenes with room-based organization
- **Sensors**: Support for Crestron Home sensors:
  - Occupancy sensors (binary sensors for presence detection)
  - Door sensors (binary sensors with battery level reporting)
  - Photo sensors (illuminance measurement in lux)
- **Configuration Flow**: Easy setup through the Home Assistant UI
- **Automatic Discovery**: Automatically discovers all compatible devices
- **Room-Based Organization**: Devices are automatically organized by room on the Home Assistant dashboard

### Supported Device Types

| Crestron Device Subtype | Home Assistant Entity | Features | Testing Status |
|-------------------------|------------------------|----------|----------------|
| Dimmer                  | Light                  | On/Off, Brightness | Tested |
| Switch                  | Light                  | On/Off | Tested |
| Shade                   | Cover                  | Open/Close, Position | Tested |
| Scene                   | Scene                  | Activate | Tested |
| OccupancySensor         | Binary Sensor         | Occupancy detection | Tested |
| DoorSensor              | Binary Sensor         | Door open/closed status, Battery level | Not tested |
| PhotoSensor             | Sensor                | Light level measurement (lux) | Not tested |

> **Note**: The OccupancySensor implementation has been thoroughly tested and works well with Crestron Home systems. The DoorSensor and PhotoSensor implementations are included but have not been tested with actual hardware yet.

## Installation

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS > Integrations > Click the three dots in the top right corner > Custom repositories
3. Add the URL of this repository and select "Integration" as the category
4. Click "Add"
5. Search for "Crestron Home" in the HACS Integrations page
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Download the latest release from the GitHub repository
2. Extract the `custom_components/crestron_home` directory into your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Getting an API Token

![Crestron Home Integration](https://raw.githubusercontent.com/ruudruud/ha-crestron-home/main/images/web-api-settings.png)

1. Open the Crestron Home Setup app
2. Go to Settings > System Settings > Web API
3. Enable the Web API
4. Generate a new API token
5. Copy the token for use in the integration setup

### Setting up the Integration

1. Go to Home Assistant > Settings > Devices & Services
2. Click "Add Integration"
3. Search for "Crestron Home"
4. Enter the following information:
   - **Host**: The IP address or hostname of your Crestron Home processor
   - **API Token**: The token you generated in the Crestron Home Setup app
   - **Update Interval**: How often to poll for updates (in seconds)
     - Default: 30 seconds, Minimum: 10 seconds
     - Lower values provide more responsive updates but increase system load
   - **Device Types to Include**: Select which types of devices to include
     - Lights: All dimmers and switches
     - Shades: All motorized shades/covers
     - Scenes: All scenes defined in your Crestron Home system
     - Binary Sensors: Occupancy sensors and door sensors
     - Sensors: Photosensors and other measurement devices
5. Click "Submit"

## Usage Examples

### Example Automation: Turn on Lights at Sunset

```yaml
automation:
  - alias: "Turn on Crestron lights at sunset"
    trigger:
      platform: sun
      event: sunset
    action:
      service: light.turn_on
      target:
        entity_id: light.living_room_main_light
      data:
        brightness_pct: 75
```

### Example Automation: Activate Scene with Voice Command

```yaml
automation:
  - alias: "Activate Movie Scene with Voice Command"
    trigger:
      platform: conversation
      command: "movie time"
    action:
      service: scene.turn_on
      target:
        entity_id: scene.living_room_movie
```

### Example Script: Control Multiple Crestron Devices

```yaml
script:
  evening_mode:
    alias: "Evening Mode"
    sequence:
      - service: light.turn_on
        target:
          entity_id: light.living_room_accent
        data:
          brightness_pct: 30
      - service: cover.set_cover_position
        target:
          entity_id: cover.living_room_shades
        data:
          position: 0
      - service: scene.turn_on
        target:
          entity_id: scene.evening_ambiance
```

### Example Automation: Using Sensors

```yaml
automation:
  - alias: "Turn on lights when motion detected"
    trigger:
      platform: state
      entity_id: binary_sensor.living_room_occupancy
      to: "on"
    condition:
      condition: numeric_state
      entity_id: sensor.living_room_photosensor
      below: 10
    action:
      service: light.turn_on
      target:
        entity_id: light.living_room_main_light
      data:
        brightness_pct: 100
```

## Requirements

- **Home Assistant Core**: Version 2024.2 or newer
- **Python**: Version 3.11 or newer
- **Dependencies**: aiohttp 3.8.0 or newer (for API communication)
- **Hardware Requirements**:
  - A Crestron Home system with CWS (Crestron Web Service) enabled
  - Network connectivity between Home Assistant and the Crestron processor
  - A valid API token for the Crestron Home system

## Technical Details

This integration:

- Uses the Crestron Home REST API to communicate with the Crestron Home system
- Implements proper session management (Crestron sessions expire after 10 minutes)
- Provides a configuration flow for easy setup through the Home Assistant UI
- Supports multiple device types with appropriate Home Assistant entity representations

## Troubleshooting

### Connection Issues

- Ensure your Crestron Home processor is reachable from your Home Assistant instance
- Verify that the Web API is enabled in the Crestron Home Setup app
- Check that the API token is valid and has not expired
- Verify that the correct host/IP is configured

### Missing Devices

- Make sure the device types you want to control are selected in the integration configuration
- Verify that the devices are properly configured in your Crestron Home system
- Try increasing the update interval to ensure all devices are discovered

### Device Type Configuration

When you configure the integration, you can select which device types (lights, shades, scenes, sensors) to include. Here's what happens when you change these settings:

- **Adding Device Types**: When you add a device type, the integration will discover and add all devices of that type to Home Assistant.
- **Removing Device Types**: When you remove a device type, all entities of that type will be completely removed from Home Assistant. This ensures your Home Assistant instance stays clean without orphaned entities.
- **Re-adding Device Types**: If you later re-add a device type, the entities will be recreated with default settings.

> **Note**: Any customizations you made to entities (such as custom names, icons, or area assignments) will be lost when you remove their device type from the configuration. These settings will need to be reapplied if you re-add the device type later.

## Contributing

Contributions are welcome! Please see the [Contributing Guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See the [Changelog](CHANGELOG.md) for a history of changes to this integration.

## Acknowledgments

This project was inspired by and adapted from the [Homebridge Crestron Home plugin](https://github.com/evgolsh/homebridge-crestron-home).

## Disclaimer

This integration is an independent project and is not affiliated with, endorsed by, or approved by Crestron Electronics, Inc. All product names, trademarks, and registered trademarks are the property of their respective owners. The use of these names, trademarks, and brands does not imply endorsement.​

This software is provided "as is," without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.​

Users are responsible for ensuring that their use of this integration complies with all applicable laws and regulations, as well as any agreements they have with third parties, including Crestron Electronics, Inc. It is the user's responsibility to obtain any necessary permissions or licenses before using this integration.​

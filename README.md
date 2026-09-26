# Home Assistant Integration for Crestron Home

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/ruudruud/ha-crestron-home.svg)](https://github.com/ruudruud/ha-crestron-home/releases)
[![GitHub License](https://img.shields.io/github/license/ruudruud/ha-crestron-home.svg)](LICENSE)

This repository contains a custom component for Home Assistant that integrates with Crestron Home systems. It allows you to control your Crestron Home devices (lights, shades, scenes) and monitor sensors through Home Assistant.

## Features

- **Lights**: Control Crestron Home lights (dimmers with brightness control, switches with on/off)
- **Shades**: Control Crestron Home shades (open, close, set position)
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

Shade stopping sends the last polled position as a new target; it is not a dedicated stop command and may move the shade back toward that position.

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
2. Go to Settings (called Installer Settings)
3. Tap System Control Options
4. Tap Web API Settings
5. Enable the Web API and generate a new API token
6. Copy the token for use in the integration setup

### Setting up the Integration

1. Go to Home Assistant > Settings > Devices & services
2. Click "Add Integration"
3. Search for "Crestron Home"
4. Enter the following information:
   - **Host**: The IP address or hostname of your Crestron Home processor
   - **API Token**: The token you generated in the Crestron Home Setup app
   - **Update Interval**: How often to poll for updates (in seconds)
     - Default: 15 seconds, minimum: 10 seconds
     - Lower values provide more responsive updates but increase system load
   - **Device Types to Include**: Select which types of devices to include
     - Lights: All dimmers and switches
     - Shades: All motorized shades/covers
     - Scenes: All scenes defined in your Crestron Home system
     - Binary Sensors: Occupancy sensors and door sensors
     - Sensors: Photosensors and other measurement devices
   - **Hide pattern** (optional): Add one pattern per entry to hide matching entities
     - Matching is case-insensitive and checks the full name (room and device name) and device type
     - Use `%` at the start or end (e.g., `%bathroom%` matches names containing "bathroom")
     - Matching entities are still created and polled. Removing a pattern unhides them unless you manually hid them.
5. Click "Submit"
6. Please allow for some time for the device synchronization.

## Requirements

- **Home Assistant Core**: Version 2026.8 or newer
- **Dependencies**: aiohttp 3.8.0 or newer (for API communication)
- **Hardware Requirements**:
  - A Crestron Home system with CWS (Crestron Web Service) enabled
  - Network connectivity between Home Assistant and the Crestron processor
  - A valid API token for the Crestron Home system

## How It Works

The integration polls the Crestron Home REST API over HTTPS at the configured interval. Displayed states reflect the last successful poll. Failed polls mark entities unavailable; a successful poll restores availability, subject to each device's reported connection status.

Requests time out after 10 seconds. Instant light commands retry once if the server disconnects; transitions, shades, and scenes are not retried. Session authentication is renewed automatically.

### Debug Script

The integration includes a standalone debug script (`scripts/crestron_debug.py`) that connects directly to your Crestron Home system and displays device information in formatted tables. This is useful for troubleshooting without involving Home Assistant.

```bash
python3 scripts/crestron_debug.py --host <crestron_host> --token <api_token>
```

Options:

- `--host`: IP address or hostname of the Crestron Home system
- `--token`: API token for authentication
- `--room`: Filter devices by room name
- `--sort`: Sort by `name`, `room`, `status`, or `level` (default: `room`)
- `--lights`: Show only lights (dimmers and switches)
- `--sensors`: Show only sensors (occupancy, door, photo)
- `--raw`: Show raw API data instead of formatted tables

Host and token can also be set as `HOST` and `TOKEN` in a `.env` file in the repository root.

## Troubleshooting

### Connection Issues

- Ensure your Crestron Home processor is reachable from your Home Assistant instance
- Verify that the Web API is enabled in the Crestron Home Setup app
- Check that the API token is valid and has not expired
- Verify that the correct host/IP is configured

### Missing Devices

- Make sure the device types you want to control are selected in the integration configuration
- Verify that the devices are properly configured in your Crestron Home system
- Try reloading the integration to re-discover devices

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

## API Documentation

Detailed Crestron Home REST API documentation is available in the [docs](docs/) directory.

## Changelog

See the [Changelog](CHANGELOG.md) for a history of changes to this integration.

## Acknowledgments

This project was inspired by and adapted from the [Homebridge Crestron Home plugin](https://github.com/evgolsh/homebridge-crestron-home).

## Disclaimer

This integration is an independent project and is not affiliated with, endorsed by, or approved by Crestron Electronics, Inc. All product names, trademarks, and registered trademarks are the property of their respective owners. The use of these names, trademarks, and brands does not imply endorsement.​

This software is provided "as is," without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.​

Users are responsible for ensuring that their use of this integration complies with all applicable laws and regulations, as well as any agreements they have with third parties, including Crestron Electronics, Inc. It is the user's responsibility to obtain any necessary permissions or licenses before using this integration.​

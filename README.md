# Home Assistant Integration for Crestron Home

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/ruudruud/ha-crestron-home.svg)](https://github.com/ruudruud/ha-crestron-home/releases)
[![GitHub License](https://img.shields.io/github/license/ruudruud/ha-crestron-home.svg)](LICENSE)

This repository contains a custom component for Home Assistant that integrates with Crestron Home systems. It allows you to control your Crestron Home devices (lights, shades, scenes) through Home Assistant.

## Overview

The integration communicates with the Crestron Home CWS (Crestron Web Service) server via HTTP to discover and control devices in your Crestron Home system.

## Features

- **Lights**: Control Crestron Home lights (on/off, brightness)
- **Shades**: Control Crestron Home shades (open, close, set position)
- **Scenes**: Activate Crestron Home scenes
- **Configuration Flow**: Easy setup through the Home Assistant UI
- **Automatic Discovery**: Automatically discovers all compatible devices

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
   - Host: The IP address or hostname of your Crestron Home processor
   - API Token: The token you generated in the Crestron Home Setup app
   - Update Interval: How often to poll for updates (in seconds)
   - Device Types to Include: Select which types of devices to include (lights, shades, scenes)
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

## Requirements

- Home Assistant Core ≥ 2024.2
- Python 3.11+
- A Crestron Home system with CWS (Crestron Web Service) enabled
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

## Contributing

Contributions are welcome! Please see the [Contributing Guidelines](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See the [Changelog](CHANGELOG.md) for a history of changes to this integration.

## Acknowledgments

This project was inspired by and adapted from the [Homebridge Crestron Home plugin](https://github.com/evgolsh/homebridge-crestron-home).

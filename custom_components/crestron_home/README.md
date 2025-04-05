# Crestron Home Integration for Home Assistant

This custom component integrates Crestron Home with Home Assistant, allowing you to control your Crestron Home devices through Home Assistant.

## Features

- Control Crestron Home lights (on/off, brightness)
- Control Crestron Home shades (open, close, set position)
- Activate Crestron Home scenes

## Requirements

- Home Assistant Core ≥ 2024.2
- Python 3.11+
- A Crestron Home system with CWS (Crestron Web Service) enabled
- A valid API token for the Crestron Home system

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

## Usage

Once configured, your Crestron Home devices will appear in Home Assistant as entities:

- Lights will appear as light entities
- Shades will appear as cover entities
- Scenes will appear as scene entities

You can control these entities through the Home Assistant UI, automations, scripts, and services.

### Example YAML Configuration

```yaml
# Example automation to turn on a Crestron light
automation:
  - alias: "Turn on Crestron light at sunset"
    trigger:
      platform: sun
      event: sunset
    action:
      service: light.turn_on
      target:
        entity_id: light.living_room_main_light

# Example automation to activate a Crestron scene
automation:
  - alias: "Activate Movie Scene when media player starts"
    trigger:
      platform: state
      entity_id: media_player.living_room_tv
      to: "playing"
    action:
      service: scene.turn_on
      target:
        entity_id: scene.living_room_movie
```

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

### Enabling Debug Logging

To get more detailed information about what's happening with the integration, you can enable debug logging:

1. Add the following to your `configuration.yaml` file:

```yaml
logger:
  default: info
  logs:
    custom_components.crestron_home: debug
```

2. Restart Home Assistant
3. Check the logs for detailed information about device discovery and communication with the Crestron system

The debug logs will show:
- Which device types are enabled
- How many devices are found in each category
- Which devices are being added to Home Assistant and which are being skipped
- Any errors that occur during communication with the Crestron system

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.

## License

This integration is licensed under the MIT License.

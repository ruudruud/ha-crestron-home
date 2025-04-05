# Home Assistant Integration for Crestron Home

This repository contains a custom component for Home Assistant that integrates with Crestron Home systems. It allows you to control your Crestron Home devices (lights, shades, scenes) through Home Assistant.

## Overview

The integration communicates with the Crestron Home CWS (Crestron Web Service) server via HTTP to discover and control devices in your Crestron Home system.

## Features

- **Lights**: Control Crestron Home lights (on/off, brightness)
- **Shades**: Control Crestron Home shades (open, close, set position)
- **Scenes**: Activate Crestron Home scenes

## Installation & Configuration

For detailed installation and configuration instructions, please see the [component README](custom_components/crestron_home/README.md).

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This project was inspired by and adapted from the [Homebridge Crestron Home plugin](https://github.com/yourusername/homebridge-crestron-home).

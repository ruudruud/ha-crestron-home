# Crestron Home for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/ruudruud/ha-crestron-home.svg)](https://github.com/ruudruud/ha-crestron-home/releases)
[![GitHub License](https://img.shields.io/github/license/ruudruud/ha-crestron-home.svg)](LICENSE)

Control Crestron Home lights, shades, thermostats, and scenes, and monitor sensors through Home Assistant. Devices are discovered over the local HTTPS API; states update by polling, every 15 seconds by default.

## Requirements

- Home Assistant **2026.8 or newer**.
- A reachable Crestron Home processor with its Web API enabled and a valid API token.

## Supported devices

| Device | HA entity | Features | Hardware tested |
|--------|-----------|----------|-----------------|
| Dimmer | Light | On/off, brightness | Yes |
| Switch | Light | On/off | Yes |
| Shade | Cover | Open/close, position | Yes |
| Drape | Cover | Open/close, position | No |
| Thermostat | Climate | Temperature, setpoints, system and fan modes | No |
| Scene | Scene | Activate | Yes |
| Occupancy sensor | Binary sensor | Occupancy | Yes |
| Door sensor | Binary sensor | Open/closed, battery status | No |
| Photo sensor | Sensor | Illuminance | No |

## 1. Install

With [HACS installed](https://www.hacs.xyz/docs/use/download/download/), open the button below, download **Crestron Home**, then **restart Home Assistant**.

[![Open Crestron Home in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ruudruud&repository=ha-crestron-home&category=integration)

**Manual installation:** Download and extract the [latest release](https://github.com/ruudruud/ha-crestron-home/releases/latest), copy `custom_components/crestron_home` into your HA configuration's `custom_components` directory, then restart Home Assistant.

## 2. Add the integration

1. In the Crestron Home Setup app, open **Installer Settings → System Control Options → Web API Settings**. Enable the API and copy its token. [Screenshot](images/web-api-settings.png)
2. Open the button below, or go to **Settings → Devices & services → Add integration → Crestron Home**.
3. Enter the processor's IP address or hostname and API token, select device types, and submit.

[![Add Crestron Home to Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=crestron_home)

## Options

Thermostats are opt-in under device types. Scheduling is not supported; temperature controls require recognised units and reported limits.

- **Update interval:** Defaults to 15 seconds; minimum 10. Shorter intervals increase processor traffic.
- **Hide patterns:** One pattern per entry, matched case-insensitively against room/device names and device types. `%example%` matches text containing “example”; `%` also works at just the start or end. Hidden entities remain polled. Removing a pattern unhides them unless you hid them manually.

Deselecting a device type removes its entities and their customizations. Re-enabling it creates them with default settings.

## Troubleshooting

For bug reports, use the integration’s **Download diagnostics** action. It exports cached device capabilities and state without names, identifiers, addresses or credentials.

- **Connection failures:** Check processor reachability, host settings, Web API access, and the token. Inspect HA logs for `crestron_home` errors. Entities recover automatically when successful polling resumes and devices report available.
- **Missing devices:** Check selected device types, hide patterns, and the Crestron configuration. Reload the integration to discover newly added devices.
- **Known limitations:** Drapes, thermostats, door and photo sensors have not been verified on hardware. Shade stopping targets the last polled position rather than issuing a dedicated stop command, so the shade may move back toward that position.

### Debug script

Inspect the API directly from a checkout of this repository:

```sh
pip install -r requirements.txt
python3 scripts/crestron_debug.py --host <host> --token <token>
python3 scripts/crestron_debug.py --help
```

Alternatively, set `HOST` and `TOKEN` in a `.env` file in the repository root. See `--help` for filters and output options.

## Project

[API reference](docs/) · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [MIT license](LICENSE)

Inspired by the [Homebridge Crestron Home plugin](https://github.com/evgolsh/homebridge-crestron-home).

This is an independent project, not affiliated with or endorsed by Crestron Electronics, Inc.

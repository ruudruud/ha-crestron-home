# Changelog

## 0.1.5 (2025-05-04)

### Bug Fixes

- Fixed warning about blocking call to `load_default_certs` in the event loop by moving SSL context creation to initialization

## 0.1.4 (2025-05-04)

### Features

- Added room name synchronization: entity names are now automatically updated when room names are changed in the Crestron Home app
- Room names are checked every 10 update cycles (approximately every 2.5 minutes with the default 15-second update interval)

## 0.1.3 (2025-05-04)

### Improvements

- Fixed issue where entities remained in Home Assistant after removing their device type from configuration

## 0.1.2 (2025-05-04)

### Improvements

- Added room-based organization for devices on the Home Assistant dashboard

## 0.1.1 (2025-05-04)

### Bug Fixes

- Fixed device discovery issue where no devices were being detected
- Added proper mapping between Crestron device types and Home Assistant device types

## 0.1.0 (2025-05-04)

### Initial Release

- Support for Crestron Home lights (on/off, brightness)
- Support for Crestron Home shades (open, close, set position)
- Support for Crestron Home scenes
- Configuration flow for easy setup
- Automatic device discovery

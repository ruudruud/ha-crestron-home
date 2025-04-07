# Changelog

## 0.2.0 (2025-07-04)

### Features

- Added intermediate abstraction layer between Crestron Home API and Home Assistant
- Implemented consistent device snapshot with improved state tracking
- Added support for device visibility and enabled logic
- Improved data model with standardized fields across device types

### Improvements

- Refactored coordinator to use the new abstraction layer
- Updated entity classes to work with the new device model
- Improved error handling and logging
- Enhanced documentation with technical details about the abstraction layer

## 0.1.5 (2025-05-04)

### Bug Fixes

- Fixed warning about blocking call to `load_default_certs` in the event loop by moving SSL context creation to initialization

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

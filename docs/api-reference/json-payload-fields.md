# JSON Payload Fields

This section describes the JSON payload fields used in the Crestron Home OS REST API responses and requests.

## Rooms

| Field | Description |
|-------|-------------|
| name | The Crestron Home room name. |
| id | The unique room ID within the Crestron Home system. |

## Devices (Generic)

| Field | Description |
|-------|-------------|
| name | The device or scene name. |
| type | The device type (light, shade, media room, lock, thermostat, security device, sensor). |
| subType | The device subtype (varies by parent device type). |
| id | The unique device ID within the Crestron Home system. |
| roomId | The unique ID of the room within the Crestron Home system. |

## Lights

| Field | Description |
|-------|-------------|
| level | An integer value (0-65535) corresponding with the lighting load level. |
| name | The lighting load name. |
| subType | The device subtype (dimmer, switch). |
| id | The unique lighting load ID within the Crestron Home system. |
| roomId | The unique ID of the room containing the lighting load. |

## Shades

| Field | Description |
|-------|-------------|
| position | An integer value (0-65535) corresponding with the shade position. |
| name | The shade name. |
| subType | The device subtype (shade, drape). |
| id | The unique shade ID within the Crestron Home system. |
| roomId | The unique ID of the room containing the shade. |

## Scenes

| Field | Description |
|-------|-------------|
| status | The current status of the scene (active, inactive). |
| name | The scene name. |
| type | The scene type (media, climate, lock, lighting, shade, shade group, I/O, daylight, generic I/O, none). |
| id | The unique scene ID within the Crestron Home system. |
| roomId | The unique ID of the room containing the scene. |

## Thermostats

| Field | Description |
|-------|-------------|
| setpoint | Object containing Type (heat, cool, auto) and Temp (setpoint temperature as an integer value). |
| mode | The thermostat operating mode (heat, cool, auto, off). |
| currentFanMode | The current fan operating mode (auto, on). |
| schedule | The thermostat schedule mode (run, hold, off). |
| currentTemperature | The current temperature observed by the thermostat. |
| temperatureUnits | The temperature unit used (Fahrenheit whole degrees, Celsius whole degrees, Celsius half degrees). |
| schedulerState | The current scheduler mode state (hold, run, off). |
| availableFanModes | The fan modes available (auto, on, low, medium, high). |
| availableSystemModes | The system modes available (off, cool, heat, auto, aux heat). |
| availableSetPoints | The setpoints available (heat, cool, auto, aux heat). |
| name | The thermostat name. |
| id | The unique thermostat ID within the Crestron Home system. |
| roomId | The unique ID of the room containing the thermostat. |

## Door Locks

| Field | Description |
|-------|-------------|
| status | The door lock state (locked, unlocked). |
| name | The door lock name. |
| id | The unique door lock ID within the Crestron Home system. |
| roomId | The unique ID of the room containing the door lock. |

## Sensors (Read-Only)

| Field | Description |
|-------|-------------|
| presence | The state of the sensor. For occupancy sensors: occupied, vacant, unavailable. For doors/gates: open or on. |
| level | For photo sensors, the operation level of the sensor (as an integer). |
| name | The sensor name. |
| subType | The sensor subtype (photo sensor, occupancy sensor). |
| id | The unique sensor ID within the Crestron Home system. |
| roomId | The unique ID of the room containing the sensor. |

## Security Devices

| Field | Description |
|-------|-------------|
| availableStates | The states available on the security device (alarm, arm away, arm instant, arm stay, disarmed, entry delay, exit delay, fire). |
| currentState | The current state of the security device. |
| name | The security device name. |
| id | The unique security device ID within the Crestron Home system. |
| roomId | The unique ID of the room containing the security device. |

## Media Rooms

| Field | Description |
|-------|-------------|
| currentVolumeLevel | The current volume level of the media device (as an integer). |
| currentSourceId | The source provider set on the media device. |
| currentMuteState | The current mute state of the device (muted, unmuted). |
| availablePowerStates | The power states available (on, off). |
| currentPowerState | The current power state of the device (on, off). |
| availableSources | A list of available media sources in the media zone. |
| availableVolumeControls | The volume controls available in the media zone (discrete). |
| schedulerState | The current scheduler mode state (hold, run, off). |
| name | The media room name. |
| id | The unique media room ID within the Crestron Home system. |
| roomId | The unique ID of the room operating as the media room. |

## Quick Actions

| Field | Description |
|-------|-------------|
| name | The name of the quick action within the Crestron Home system. |
| id | The unique quick action ID within the Crestron Home system. |

## Error Objects

| Field | Description |
|-------|-------------|
| errorSource | The source at which the error occurred (see error source codes below). |
| errorMessage | A generic message regarding the error. |

### Error Source Codes

| Code | Description |
|------|-------------|
| 5001 | Session expired |
| 5002 | Authentication |
| 6001 | Rooms |
| 7000 | Unhandled |
| 7001 | Login |
| 7003 | Lights |
| 7004 | Shades |
| 7005 | Logout |
| 7006 | Scenes |
| 7007 | Thermostats |
| 7008 | Fan mode |
| 7009 | System mode |
| 8000 | Invalid data |
| 8001 | Devices |
| 8005 | Security devices |
| 8006 | Sensors |
| 8007 | Door locks |
| 8008 | Scheduler |
| 8009 | Setpoint |
| 8010 | Media rooms |

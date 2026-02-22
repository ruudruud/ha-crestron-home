# Devices API

The Devices API retrieves information about all available devices in the Crestron Home OS system.

## GET devices

Retrieves all available devices in the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/devices

### Parameters

None

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response

Response Type: Application/JSON

```json
{
  "devices": [
    {
      "id": 10,
      "name": "Device Name",
      "type": "light",
      "subType": "Dimmer",
      "roomId": 1
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| devices | array | A collection of device objects. |
| devices[].id | integer | The unique identifier for the device. |
| devices[].name | string | The display name of the device. |
| devices[].type | string | The device category. Possible values: light, shade, thermostat, lock, sensor, securityDevice, mediaZone. |
| devices[].subType | string | The device subtype. Possible values: Dimmer, Switch, Shade, OccupancySensor, PhotoSensor, Audio. |
| devices[].roomId | integer | The identifier of the room the device is associated with. |
| version | string | The API version identifier. |

## GET devices/{id}

Retrieves information for a specific device.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/devices/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the device in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response

Response Type: Application/JSON

```json
{
  "devices": [
    {
      "id": 10,
      "name": "Device Name",
      "type": "light",
      "subType": "Dimmer",
      "roomId": 1
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| devices | array | A collection containing the requested device object. |
| devices[].id | integer | The unique identifier for the device. |
| devices[].name | string | The display name of the device. |
| devices[].type | string | The device category. |
| devices[].subType | string | The device subtype. |
| devices[].roomId | integer | The identifier of the room the device is associated with. |
| version | string | The API version identifier. |

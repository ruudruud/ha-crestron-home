# Sensors API

The Sensors API is used to obtain information for sensors within the Crestron Home® OS system.

## GET sensors

This method gets a list of all available sensors within the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/sensors

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
  "sensors": [
    {
      "presence": "Unavailable",
      "id": 7,
      "name": "GLS-OIR-sensor",
      "subType": "OccupancySensor",
      "roomId": 2
    },
    {
      "level": 0,
      "id": 11,
      "name": "Photosensor",
      "subType": "PhotoSensor",
      "connectionStatus": "online",
      "roomId": 5
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| presence | string | The occupancy state (e.g., "Unavailable"). Present on OccupancySensor sub-types. |
| level | integer | The sensor level reading. Present on PhotoSensor sub-types. |
| door_status | string | The door state (e.g., "Closed"). Present on DoorSensor sub-types. |
| battery_level | string | The battery level (e.g., "Normal"). Present on DoorSensor sub-types. |
| id | integer | Unique identifier for the sensor. |
| name | string | Display name of the sensor. |
| subType | string | The sensor sub-type: "OccupancySensor", "PhotoSensor", "DoorSensor", etc. |
| connectionStatus | string | The connection status of the sensor (e.g., "online"). |
| roomId | integer | The identifier of the room the sensor belongs to. |
| version | string | The API version. |

## GET sensors/{id}

This method gets information for a specific sensor within the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/sensors/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the sensor in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response

Response Type: Application/JSON

```json
{
  "sensors": [
    {
      "door_status": "Closed",
      "battery_level": "Normal",
      "id": 55,
      "name": "D",
      "subType": "DoorSensor",
      "roomId": 52
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| door_status | string | The door state (e.g., "Closed"). Present on DoorSensor sub-types. |
| battery_level | string | The battery level (e.g., "Normal"). Present on DoorSensor sub-types. |
| id | integer | Unique identifier for the sensor. |
| name | string | Display name of the sensor. |
| subType | string | The sensor sub-type (e.g., "DoorSensor"). |
| roomId | integer | The identifier of the room the sensor belongs to. |
| version | string | The API version. |

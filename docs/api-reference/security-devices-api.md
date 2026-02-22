# Security Devices API

The Security Devices API is used to obtain information for security devices within the Crestron Home OS system.

## GET securitydevices

Retrieves all available security devices and their current status.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/securitydevices

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
  "securityDevices": [
    {
      "availableStates": [
        "Alarm",
        "ArmAway",
        "ArmInstant",
        "ArmStay",
        "Disarmed",
        "EntryDelay",
        "ExitDelay",
        "Fire"
      ],
      "currentState": "Disarmed",
      "id": 14,
      "name": "Honeywell",
      "connectionStatus": "online",
      "roomId": 1
    }
  ],
  "version": ""
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| securityDevices | array | An array of security device objects in the system. |
| availableStates | array of strings | The states available on the security device (Alarm, ArmAway, ArmInstant, ArmStay, Disarmed, EntryDelay, ExitDelay, Fire). |
| currentState | string | The current state of the security device. |
| id | integer | The unique security device ID within the Crestron Home system. |
| name | string | The security device name. |
| connectionStatus | string | The connection status of the device (e.g., "online"). |
| roomId | integer | The unique ID of the room containing the security device. |
| version | string | The API version. |

## GET securitydevices/{id}

Retrieves information for a specific security device by its unique identifier.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/securitydevices/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the security device in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response

Response Type: Application/JSON

```json
{
  "securityDevices": [
    {
      "availableStates": [
        "Alarm",
        "ArmAway",
        "ArmInstant",
        "ArmStay",
        "Disarmed",
        "EntryDelay",
        "ExitDelay",
        "Fire"
      ],
      "currentState": "Disarmed",
      "id": 14,
      "name": "Honeywell",
      "connectionStatus": "online",
      "roomId": 1
    }
  ],
  "version": ""
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| securityDevices | array | An array containing the requested security device object. |
| availableStates | array of strings | The states available on the security device (Alarm, ArmAway, ArmInstant, ArmStay, Disarmed, EntryDelay, ExitDelay, Fire). |
| currentState | string | The current state of the security device. |
| id | integer | The unique security device ID within the Crestron Home system. |
| name | string | The security device name. |
| connectionStatus | string | The connection status of the device (e.g., "online"). |
| roomId | integer | The unique ID of the room containing the security device. |
| version | string | The API version. |

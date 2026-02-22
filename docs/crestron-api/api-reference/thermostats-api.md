# Thermostats API

The Thermostats API is used to obtain information for thermostats within the Crestron Home® OS system and to perform certain actions for thermostats.

## GET thermostats

This method gets a list of all available thermostats within the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/thermostats

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
  "thermostats": [
    {
      "mode": "Cool",
      "setPoint": {
        "type": "Cool",
        "temperature": 770,
        "minValue": 590,
        "maxValue": 990
      },
      "currentTemperature": 760,
      "temperatureUnits": "FahrenheitWholeDegrees",
      "currentFanMode": "Auto",
      "schedulerState": "run",
      "availableFanModes": [
        "Auto",
        "On"
      ],
      "availableSystemModes": [
        "Off",
        "Cool",
        "Heat"
      ],
      "availableSetPoints": [
        {
          "type": "Heat",
          "minValue": 380,
          "maxValue": 890
        },
        {
          "type": "Cool",
          "minValue": 590,
          "maxValue": 990
        }
      ],
      "id": 15,
      "name": "CTSTAT",
      "roomId": 1
    },
    {
      "mode": "0",
      "setPoint": {
        "type": "Off"
      },
      "temperature": 0,
      "temperatureUnits": "FahrenheitWholeDegrees",
      "currentFanMode": "Auto",
      "schedulerState": "run",
      "availableFanModes": [
        "Auto",
        "High"
      ],
      "availableSystemModes": [
        "Off"
      ],
      "availableSetPoints": [],
      "id": 13,
      "name": "TSTAT",
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
| mode | string | The current operating mode of the thermostat (e.g., "Cool", "Heat", "Off"). |
| setPoint | object | The current set point configuration. |
| setPoint.type | string | The type of set point (e.g., "Cool", "Heat", "Auto", "Off"). |
| setPoint.temperature | integer | The target temperature value (e.g., 770 represents 77.0 degrees). |
| setPoint.minValue | integer | The minimum allowable temperature value for the current set point. |
| setPoint.maxValue | integer | The maximum allowable temperature value for the current set point. |
| currentTemperature | integer | The current temperature reading (e.g., 760 represents 76.0 degrees). |
| temperatureUnits | string | The unit of temperature measurement (e.g., "FahrenheitWholeDegrees"). |
| currentFanMode | string | The current fan mode (e.g., "Auto", "On", "High"). |
| schedulerState | string | The current scheduler state ("run" or "hold"). |
| availableFanModes | array of strings | List of supported fan modes for this thermostat. |
| availableSystemModes | array of strings | List of supported operating modes for this thermostat. |
| availableSetPoints | array of objects | List of possible set point configurations with type, minValue, and maxValue. |
| id | integer | Unique identifier for the thermostat. |
| name | string | Display name of the thermostat. |
| connectionStatus | string | The connection status of the thermostat (e.g., "online"). |
| roomId | integer | The identifier of the room the thermostat belongs to. |
| version | string | The API version. |

## GET thermostats/{id}

This method gets information for a specific thermostat within the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/thermostats/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the thermostat in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response

Response Type: Application/JSON

```json
{
  "thermostats": [
    {
      "mode": "Cool",
      "setPoint": {
        "type": "Cool",
        "temperature": 770,
        "minValue": 590,
        "maxValue": 990
      },
      "currentTemperature": 760,
      "temperatureUnits": "FahrenheitWholeDegrees",
      "currentFanMode": "Auto",
      "schedulerState": "run",
      "availableFanModes": [
        "Auto",
        "On"
      ],
      "availableSystemModes": [
        "Off",
        "Cool",
        "Heat"
      ],
      "availableSetPoints": [
        {
          "type": "Heat",
          "minValue": 380,
          "maxValue": 890
        },
        {
          "type": "Cool",
          "minValue": 590,
          "maxValue": 990
        }
      ],
      "id": 15,
      "name": "CTSTAT",
      "connectionStatus": "online",
      "roomId": 1
    }
  ],
  "version": ""
}
```

### Response Fields

Same as GET thermostats (see above).

## POST thermostats/SetPoint

This method modifies the temperature set point for a thermostat.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/thermostats/SetPoint

### Parameters

None

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Request Body

```json
{
  "id": "[id]",
  "setpoints": [
    {
      "type": "[Auto/Cool/Heat]",
      "temperature": "[expected threshold at which thermostat operates]"
    },
    {
      "type": "[Auto/Cool/Heat]",
      "temperature": "[expected threshold at which thermostat operates]"
    }
  ]
}
```

### Request Body Fields

| Field | Type | Description |
|-------|------|-------------|
| id | integer | The unique identifier of the thermostat. |
| setpoints | array of objects | Array of set point configurations to apply. |
| setpoints[].type | string | The type of set point: "Auto", "Cool", or "Heat". |
| setpoints[].temperature | integer | The target temperature value (e.g., 770 for 77.0 degrees). |

### Sample Responses

Response Type: Application/JSON

**Success:**

```json
{
  "status": "success",
  "version": "1.000.0001"
}
```

**Failure:**

```json
{
  "status": "failure",
  "errorMessage": "Thermostat with Id [id] has not found in the system.",
  "version": "1.000.0001"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | The result of the operation: "success" or "failure". |
| errorMessage | string | A description of the error (present on failure responses only). |
| version | string | The API version. |

## POST thermostats/mode

This method changes the operating mode of one or more thermostats.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/thermostats/mode

### Parameters

None

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Request Body

```json
{
  "thermostats": [
    {
      "id": "[id]",
      "mode": "[HEAT/COOL/AUTO/OFF]"
    },
    {
      "id": "[id]",
      "mode": "[HEAT/COOL/AUTO/OFF]"
    }
  ]
}
```

### Request Body Fields

| Field | Type | Description |
|-------|------|-------------|
| thermostats | array of objects | Array of thermostat mode changes. |
| thermostats[].id | integer | The unique identifier of the thermostat. |
| thermostats[].mode | string | The target operating mode: "HEAT", "COOL", "AUTO", or "OFF". |

### Sample Responses

Response Type: Application/JSON

**Success:**

```json
{
  "status": "success",
  "version": "1.000.0001"
}
```

**Partial Success:**

```json
{
  "status": "partial",
  "errorMessage": "Thermostat(s) with below Id(s) are failed to set mode.",
  "errorDevices": [1, 2],
  "version": "1.000.0001"
}
```

**Failure:**

```json
{
  "status": "failure",
  "errorMessage": "Thermostat(s) with below Id(s) are failed to set mode.",
  "errorDevices": [1, 2, 3],
  "version": "1.000.0001"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | The result of the operation: "success", "partial", or "failure". |
| errorMessage | string | A description of the error (present on partial or failure responses). |
| errorDevices | array of integers | List of thermostat IDs that failed to update (present on partial or failure responses). |
| version | string | The API version. |

## POST thermostats/fanmode

This method changes the fan mode of one or more thermostats.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/thermostats/fanmode

### Parameters

None

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Request Body

```json
{
  "thermostats": [
    {
      "id": "[id]",
      "mode": "[AUTO/ON]"
    },
    {
      "id": "[id]",
      "mode": "[AUTO/ON]"
    }
  ]
}
```

### Request Body Fields

| Field | Type | Description |
|-------|------|-------------|
| thermostats | array of objects | Array of thermostat fan mode changes. |
| thermostats[].id | integer | The unique identifier of the thermostat. |
| thermostats[].mode | string | The target fan mode: "AUTO" or "ON". |

### Sample Responses

Response Type: Application/JSON

**Success:**

```json
{
  "status": "success",
  "version": "1.000.0001"
}
```

**Partial Success:**

```json
{
  "status": "partial",
  "errorMessage": "Thermostat(s) with below Id(s) are failed to set mode.",
  "errorDevices": [1, 2],
  "version": "1.000.0001"
}
```

**Failure:**

```json
{
  "status": "failure",
  "errorMessage": "Thermostat(s) with below Id(s) are failed to set mode.",
  "errorDevices": [1, 2, 3],
  "version": "1.000.0001"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | The result of the operation: "success", "partial", or "failure". |
| errorMessage | string | A description of the error (present on partial or failure responses). |
| errorDevices | array of integers | List of thermostat IDs that failed to update (present on partial or failure responses). |
| version | string | The API version. |

## POST thermostats/schedule

This method changes the scheduler state of one or more thermostats.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/thermostats/schedule

### Parameters

None

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Request Body

```json
{
  "thermostats": [
    {
      "id": "[id]",
      "mode": "[RUN/HOLD]"
    },
    {
      "id": "[id]",
      "mode": "[RUN/HOLD]"
    }
  ]
}
```

### Request Body Fields

| Field | Type | Description |
|-------|------|-------------|
| thermostats | array of objects | Array of thermostat schedule changes. |
| thermostats[].id | integer | The unique identifier of the thermostat. |
| thermostats[].mode | string | The target scheduler state: "RUN" or "HOLD". |

### Sample Responses

Response Type: Application/JSON

**Success:**

```json
{
  "status": "success",
  "version": "1.000.0001"
}
```

**Partial Success:**

```json
{
  "status": "partial",
  "errorMessage": "Thermostat(s) with below Id(s) are failed to set mode.",
  "errorDevices": [1, 2],
  "version": "1.000.0001"
}
```

**Failure:**

```json
{
  "status": "failure",
  "errorMessage": "Thermostat(s) with below Id(s) are failed to set mode.",
  "errorDevices": [1, 2, 3],
  "version": "1.000.0001"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | The result of the operation: "success", "partial", or "failure". |
| errorMessage | string | A description of the error (present on partial or failure responses). |
| errorDevices | array of integers | List of thermostat IDs that failed to update (present on partial or failure responses). |
| version | string | The API version. |

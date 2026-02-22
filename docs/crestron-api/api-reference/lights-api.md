# Lights API

The Lights API retrieves information about lighting devices in the Crestron Home OS system and allows control of lighting state.

## GET lights

Retrieves all available lights in the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/lights

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
  "lights": [
    {
      "id": 10,
      "name": "System",
      "type": "light",
      "subType": "Dimmer",
      "level": 0,
      "connectionStatus": "online",
      "roomId": 1
    },
    {
      "id": 21,
      "name": "Zone1",
      "type": "light",
      "subType": "Switch",
      "level": 65535,
      "connectionStatus": "online",
      "roomId": 2
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| lights | array | A collection of light objects. |
| lights[].id | integer | The unique identifier for the light. |
| lights[].name | string | The display name of the light. |
| lights[].type | string | The device type (light). |
| lights[].subType | string | The light subtype. Possible values: Dimmer, Switch. |
| lights[].level | integer | The current brightness level of the light (0-65535). |
| lights[].connectionStatus | string | The connection status of the light (e.g., online). |
| lights[].roomId | integer | The identifier of the room the light is associated with. |
| version | string | The API version identifier. |

## GET lights/{id}

Retrieves information for a specific light.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/lights/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the light in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response

Response Type: Application/JSON

```json
{
  "lights": [
    {
      "id": 10,
      "name": "Zone1",
      "type": "light",
      "subType": "Dimmer",
      "level": 32768,
      "connectionStatus": "online",
      "roomId": 1
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| lights | array | A collection containing the requested light object. |
| lights[].id | integer | The unique identifier for the light. |
| lights[].name | string | The display name of the light. |
| lights[].type | string | The device type (light). |
| lights[].subType | string | The light subtype (Dimmer or Switch). |
| lights[].level | integer | The current brightness level of the light (0-65535). |
| lights[].connectionStatus | string | The connection status of the light. |
| lights[].roomId | integer | The identifier of the room the light is associated with. |
| version | string | The API version identifier. |

## POST lights/SetState

Sets the state of one or more lights. Multiple lights can be controlled in a single request.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/lights/SetState

### Parameters

None

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Request Body

Content Type: Application/JSON

```json
{
  "lights": [
    {
      "id": 10,
      "level": 65535,
      "time": 1000
    },
    {
      "id": 21,
      "level": 0,
      "time": 500
    }
  ]
}
```

### Request Body Fields

| Field | Type | Description |
|-------|------|-------------|
| lights | array | A collection of light state objects to update. |
| lights[].id | integer | The unique identifier of the light to control. |
| lights[].level | integer | The target brightness level (0-65535). |
| lights[].time | integer | The transition time in milliseconds. |

### Sample Response -- Success

Response Type: Application/JSON

```json
{
  "status": "success",
  "version": "1.000.0001"
}
```

### Sample Response -- Partial Success

```json
{
  "status": "partial",
  "errorMessage": "Light(s) with below Id(s) are failed to update.",
  "errorDevices": [20, 101],
  "version": "1.000.0001"
}
```

### Sample Response -- Failure

```json
{
  "status": "failure",
  "errorMessage": "Light(s) with below Id(s) are failed to update.",
  "errorDevices": [20, 101, 111],
  "version": "1.000.0001"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | The result of the operation. Possible values: success, partial, failure. |
| errorMessage | string | A description of the error (present when status is partial or failure). |
| errorDevices | array | A list of light IDs that failed to update (present when status is partial or failure). |
| version | string | The API version identifier. |

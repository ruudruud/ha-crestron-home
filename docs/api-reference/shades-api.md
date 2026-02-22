# Shades API

The Shades API is used to obtain information for shades within the Crestron Home® OS system and to perform certain actions for shades.

## GET shades

This method gets a list of all available shades within the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/shades

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
  "shades": [
    {
      "position": 0,
      "id": 1184,
      "name": "Midbot",
      "subType": "Shade",
      "connectionStatus": "online",
      "roomId": 1093
    },
    {
      "position": 0,
      "id": 1186,
      "name": "NorthEastShade",
      "subType": "Shade",
      "connectionStatus": "online",
      "roomId": 1097
    }
  ],
  "version": "[API Version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| position | integer | The current position of the shade (0-65535). |
| id | integer | Unique identifier for the shade. |
| name | string | Display name of the shade. |
| subType | string | The sub-type of the shade (e.g., "Shade"). |
| connectionStatus | string | The connection status of the shade (e.g., "online"). |
| roomId | integer | The identifier of the room the shade belongs to. |
| version | string | The API version. |

## GET shades/{id}

This method gets information for a specific shade within the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/shades/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the shade in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response

Response Type: Application/JSON

```json
{
  "shades": [
    {
      "id": 24,
      "name": "Zone1",
      "subType": "[shade/drape]",
      "position": "[0-65535]",
      "roomId": "[id]"
    }
  ],
  "version": "[API Version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier for the shade. |
| name | string | Display name of the shade. |
| subType | string | The sub-type of the shade (e.g., "Shade", "Drape"). |
| position | integer | The current position of the shade (0-65535). |
| roomId | integer | The identifier of the room the shade belongs to. |
| version | string | The API version. |

## POST shades/SetState

This method sets the position of one or more shades.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/shades/SetState

### Parameters

None

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Request Body

```json
{
  "shades": [
    {
      "id": "[id]",
      "position": "[0-65535]"
    },
    {
      "id": "[id]",
      "position": "[0-65535]"
    }
  ]
}
```

### Request Body Fields

| Field | Type | Description |
|-------|------|-------------|
| id | integer | The unique identifier of the shade to control. |
| position | integer | The target position for the shade (0-65535). |

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
  "errorMessage": "Shade(s) with below Id(s) are failed to update.",
  "errorDevices": [1, 2],
  "version": "1.000.0001"
}
```

**Failure:**

```json
{
  "status": "failure",
  "errorMessage": "Shade(s) with below Id(s) are failed to update.",
  "errorDevices": [1, 2, 3],
  "version": "1.000.0001"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | The result of the operation: "success", "partial", or "failure". |
| errorMessage | string | A description of the error (present on partial or failure responses). |
| errorDevices | array of integers | List of shade IDs that failed to update (present on partial or failure responses). |
| version | string | The API version. |

# Scenes API

The Scenes API is used to obtain information for preset scenes within the Crestron Home® OS system and to perform certain actions for scenes.

## GET scenes

This method gets a list of all available scenes within the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/scenes

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
  "scenes": [
    {
      "id": 1,
      "name": "All On",
      "type": "Lighting",
      "status": false,
      "roomId": 1001
    },
    {
      "id": 2,
      "name": "All Off",
      "type": "Lighting",
      "status": false,
      "roomId": 1001
    },
    {
      "id": 3,
      "name": "All On",
      "type": "Lighting",
      "status": true,
      "roomId": 2
    },
    {
      "id": 4,
      "name": "All Off",
      "type": "Lighting",
      "status": false,
      "roomId": 2
    },
    {
      "id": 5,
      "name": "Test",
      "type": "Lighting",
      "status": true,
      "roomId": 2
    },
    {
      "id": 6,
      "name": "All On",
      "type": "Lighting",
      "status": false,
      "roomId": 1
    },
    {
      "id": 7,
      "name": "All Off",
      "type": "Lighting",
      "status": false,
      "roomId": 1
    },
    {
      "id": 9,
      "name": "MasterShade",
      "type": "Shade",
      "status": false,
      "roomId": 2
    },
    {
      "id": 10,
      "name": "AtriumShade",
      "type": "Shade",
      "status": false,
      "roomId": 1
    },
    {
      "id": 11,
      "name": "All Open",
      "type": "Shade",
      "status": false,
      "roomId": 1001
    },
    {
      "id": 12,
      "name": "All Close",
      "type": "Shade",
      "status": false,
      "roomId": 1001
    },
    {
      "id": 13,
      "name": "All Open",
      "type": "Shade",
      "status": false,
      "roomId": 1
    },
    {
      "id": 14,
      "name": "All Close",
      "type": "Shade",
      "status": false,
      "roomId": 1
    },
    {
      "id": 8,
      "name": "Test",
      "type": "None",
      "status": true,
      "roomId": 1001
    },
    {
      "id": 18,
      "name": "Daylighting",
      "type": "Daylight",
      "status": false,
      "roomId": 2
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier for the scene. |
| name | string | Display name of the scene. |
| type | string | The type of scene: "Lighting", "Shade", "Daylight", or "None". |
| status | boolean | The current status of the scene. |
| roomId | integer | The identifier of the room the scene belongs to. |
| version | string | The API version. |

## GET scenes/{id}

This method gets information for a specific scene within the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/scenes/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the scene in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response

Response Type: Application/JSON

```json
{
  "scenes": [
    {
      "id": 12,
      "name": "All Close",
      "type": "Shade",
      "status": false,
      "roomId": 1001
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier for the scene. |
| name | string | Display name of the scene. |
| type | string | The type of scene: "Lighting", "Shade", "Daylight", or "None". |
| status | boolean | The current status of the scene. |
| roomId | integer | The identifier of the room the scene belongs to. |
| version | string | The API version. |

## POST scenes/recall/{id}

This method recalls (executes) a specific scene.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/scenes/recall/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the scene in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

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
  "errorMessage": "Scene with Id [id] has not found in the system.",
  "version": "1.000.0001"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | The result of the operation: "success" or "failure". |
| errorMessage | string | A description of the error (present on failure responses only). |
| version | string | The API version. |

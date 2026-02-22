# Door Locks API

The Door Locks API is used to obtain information for door locks within the Crestron Home® OS system and to perform certain actions for door locks.

## GET doorlocks

This method gets a list of all available door locks within the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/doorlocks

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
  "doorLocks": [
    {
      "status": "locked",
      "id": 7,
      "type": "lock",
      "connectionStatus": "online",
      "name": "Front Door",
      "roomId": 3
    },
    {
      "status": "unlocked",
      "id": 8,
      "type": "lock",
      "connectionStatus": "online",
      "name": "Back Door",
      "roomId": 7
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | The lock state: "locked" or "unlocked". |
| id | integer | Unique identifier for the door lock. |
| type | string | The device type (e.g., "lock"). |
| connectionStatus | string | The connection status of the door lock (e.g., "online"). |
| name | string | Display name of the door lock. |
| roomId | integer | The identifier of the room the door lock belongs to. |
| version | string | The API version. |

## GET doorlocks/{id}

This method gets information for a specific door lock within the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/doorlocks/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the door lock in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response

Response Type: Application/JSON

```json
{
  "doorLocks": [
    {
      "status": "locked",
      "id": 7,
      "type": "lock",
      "connectionStatus": "online",
      "name": "Front Door",
      "roomId": 3
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | The lock state: "locked" or "unlocked". |
| id | integer | Unique identifier for the door lock. |
| type | string | The device type (e.g., "lock"). |
| connectionStatus | string | The connection status of the door lock (e.g., "online"). |
| name | string | Display name of the door lock. |
| roomId | integer | The identifier of the room the door lock belongs to. |
| version | string | The API version. |

## POST doorlocks/lock/{id}

This method locks a specific door lock.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/doorlocks/lock/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the door lock in the system. |

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
  "errorMessage": "Door lock with Id [id] has not found in the system.",
  "version": "1.000.0001"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | The result of the operation: "success" or "failure". |
| errorMessage | string | A description of the error (present on failure responses only). |
| version | string | The API version. |

## POST doorlocks/unlock/{id}

This method unlocks a specific door lock.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/doorlocks/unlock/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the door lock in the system. |

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
  "errorMessage": "Door lock with Id [id] has not found in the system.",
  "version": "1.000.0001"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | string | The result of the operation: "success" or "failure". |
| errorMessage | string | A description of the error (present on failure responses only). |
| version | string | The API version. |

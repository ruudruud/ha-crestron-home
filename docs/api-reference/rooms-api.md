# Rooms API

The Rooms API retrieves information about rooms in the Crestron Home OS system.

## GET rooms

Retrieves all available rooms in the system.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/rooms

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
  "rooms": [
    {
      "id": 1001,
      "name": "Whole House"
    },
    {
      "id": 1,
      "name": "Atrium"
    },
    {
      "id": 2,
      "name": "Master Room"
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| rooms | array | A collection of room objects. |
| rooms[].id | integer | The unique identifier for the room. |
| rooms[].name | string | The display name of the room. |
| version | string | The API version identifier. |

## GET rooms/{id}

Retrieves information for a specific room.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/rooms/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the room in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response

Response Type: Application/JSON

```json
{
  "rooms": [
    {
      "id": 2,
      "name": "Master Room"
    }
  ],
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| rooms | array | A collection containing the requested room object. |
| rooms[].id | integer | The unique identifier for the room. |
| rooms[].name | string | The display name of the room. |
| version | string | The API version identifier. |

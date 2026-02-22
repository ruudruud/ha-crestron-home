# Quick Actions API

The Quick Actions API is used to retrieve all available quick actions within the Crestron Home OS system.

## GET quickactions

Retrieves all available quick actions.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/quickactions

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
  "quickActions": [
    {
      "id": 1,
      "name": "Good Morning"
    },
    {
      "id": 2,
      "name": "Good Night"
    }
  ],
  "version": ""
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| quickActions | array | An array of quick action objects in the system. |
| id | integer | The unique quick action ID within the Crestron Home system. |
| name | string | The name of the quick action within the Crestron Home system. |
| version | string | The API version. |

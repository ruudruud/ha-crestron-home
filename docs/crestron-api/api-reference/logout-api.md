# Logout API

The Logout API ends the active REST API session and invalidates the current authentication key.

## GET logout

This method ends the active REST API session and invalidates the current authentication key.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/logout

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
  "status": true,
  "version": "[API version]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| status | boolean | Indicates whether the session was successfully terminated. |
| version | string | The API version identifier. |

## Notes

- After logging out, the authentication key is no longer valid.
- To start a new session, a new login request must be sent with a valid authorization token.

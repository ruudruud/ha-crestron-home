# Login API

The Login API authenticates a client with the Crestron Home OS REST API and establishes a session by returning an authentication key.

## GET login

This method processes a GET request containing the authorization token and returns an authentication key for use in all subsequent API requests.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/login

### Parameters

None

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthToken | [Authorization Token] |

### Sample Response

Response Type: Application/JSON

```json
{
  "version": "2.0",
  "AuthKey": "[Authentication Key]"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| version | string | The API version identifier. |
| AuthKey | string | The authentication key to be used as an opaque identifier for all subsequent API requests. |

## Notes

- The returned `AuthKey` must be included in the `Crestron-RestAPI-AuthKey` header for all subsequent API requests.
- Token generation uses server-side crypto-random methods.
- The authentication key has an idle timeout limit. If the key is invalid or has expired, the server returns an HTTP status code of 401 (Unauthorized) or 511 (Network Authentication Required).
- For more information on generating an authorization token, refer to the Web Authorization Token documentation.

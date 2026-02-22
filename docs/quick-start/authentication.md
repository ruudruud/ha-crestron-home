# Authentication

An authorization token is required in order for the client to send requests to the REST API. This token is validated by Crestron Home, which responds with an authentication key if the validation is successful. The authentication key is used throughout the session between the client and server. To retrieve the authentication key and begin the session, the client must send a login request with the associated authorization token. For more information on generating an authorization token, refer to [Web Authorization Token](overview.md#web-authorization-token).

To end the session, the client must send a logout request. The server maintains an idle timeout limit of 10 minutes per authorization key. If the key is invalid or has expired, the server returns an HTTP status code of 401 (unauthorized) or 511 (network authentication required). When the client receives the 401 or 511 status code, the client must send a new login request to get another authentication key. Refer to the following control flow diagram.

For more information on formatting the login and logout requests, refer to [API Reference](../api-reference/README.md).

## Control Flow

1. Client sends a **GET** request to `/cws/api/login` with the `Crestron-RestAPI-AuthToken` header set to the authorization token.
2. Server validates the token and responds with an authentication key (`AuthKey`) in the JSON response.
3. Client includes the `Crestron-RestAPI-AuthKey` header with the received authentication key in all subsequent API requests.
4. The session remains active as long as requests are made within the 10-minute idle timeout.
5. If the session expires (401 or 511 response), the client must send a new login request.
6. Client sends a logout request to end the session.

## Headers

| Header | Used For | Description |
|---|---|---|
| `Crestron-RestAPI-AuthToken` | Login request | The authorization token generated from the Crestron Home setup app. Sent with the GET login request. |
| `Crestron-RestAPI-AuthKey` | All other requests | The authentication key returned by the server after a successful login. Sent with every subsequent API request. |

## Session Timeout

> **NOTE**: It is required that the authentication key has an idle timeout limit. The suggested duration for this limit is 10 minutes. If the time limit is increased, then the existing authentication key will expire. The client must send a new login request to restart communication with the server.

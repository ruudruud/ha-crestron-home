# Make API Calls

The Crestron Home OS REST API supports synchronous and asynchronous retrieval of data and synchronous setting of data.

> **NOTE**: Most of the following procedures use Postman as an example API development environment program. While these procedures can apply to any API development environment program, the actual implementation may vary by program. Refer to the program's documentation for more information on using it to make API calls.

## Root APIs

The Crestron Home REST API has three primary root API calls:

- `/cws/api/rooms`
- `/cws/api/devices`
- `/cws/api/mediarooms`

It is recommended to make calls to these APIs first before making subsequent calls to any respective loads or device types. For more information, refer to [API Reference](../api-reference/README.md).

## Getting Started

To access the Crestron Home REST API interface:

1. Open an API development environment program (such as Postman, which may be downloaded at [www.getpostman.com](https://www.getpostman.com)) that supports HTTP requests.
2. Create an authorization token and send a login request as described in [Authentication](authentication.md).
3. Issue an HTTP request that includes the required HTTP method, headers, and parameters as outlined in the sections that follow. A valid authorization token must be in place throughout the entire session. For more information, refer to [API Reference](../api-reference/README.md).

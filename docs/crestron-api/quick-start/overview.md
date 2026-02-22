# Overview

The following sections provide an introduction for working with the Crestron Home OS REST API.

## Base URI

The root path to the API begins with `/cws/api` and is followed by the chosen endpoint.

```
https://{host}/cws/api
```

The supported HTTP methods for API are GET and POST. Any documents sent through the request must be in the form of `application/json`. Every request made must have a custom header to identify the user (authorization token), except for the login request to retrieve the authentication key.

Any errors at the REST API layer will be mapped to HTTP status codes (if possible) and the respective error payload will be returned to the end client.

## JSON Data Format

The Crestron Home REST API supports synchronous retrieval of data and synchronous setting of data. This API follows the standard JSON specifications to send/receive data between the applications.

The following example shows the basic format for the JSON document sent as a response to API calls.

```json
{
  "id": json-value (),
  "version": [integer]
  ...Further device specific json fields...
}
```

- **id**: A unique ID that identifies a component of the Crestron Home system.
- **version**: The version of the REST API. It is an integer value.

Additional component-specific JSON fields are described in [JSON Payload Fields](../api-reference/json-payload-fields.md).

## Dynamic Resources

All devices in Crestron Home can be accessed using the `/api/devices` base call. For more information, refer to [Devices API](../api-reference/devices.md).

```
https://{host}/cws/api/devices
```

Once the device list has been retrieved, any requests for specific devices take the following form, where `{id}` is the unique identifier of the device in the system (returned in the `/api/devices` base call):

```
https://{host}/cws/api/devices/{id}
```

## CWS Server

The CWS Server acts as a web server for API requests and starts when Crestron Home completes its initialization process. Once the CWS server is initialized, it will start accepting the requests in a specified URL format mentioned in this document.

## Web Authorization Token

In order to initiate communication with the Crestron Home CWS server, the client must send the Login API call with an authorization token. This token is automatically generated from Crestron Home via the Crestron Home setup app. For more information, refer to [Authentication](authentication.md).

To generate an authentication token from the Crestron Home setup app:

1. Select the gear icon on the home screen to display the **Installer Settings** screen.
2. Select **System Control Options** to display additional system control settings.
3. Select **Web API Settings** to display the **Web API Settings** screen.
4. Select **Update Token** to generate a new authentication token.
5. Copy the generated token to the clipboard or another accessible location on your computer.

## Protocols and Security

Clients can communicate with current generation Crestron Home control systems (CP4-R V2 model, MC4-R, and PC4-R) using the secured HTTPS protocol, whereas older Crestron Home control systems (PYNG-HUB, CP3-R, and CP4-R V1 model) can use the nonsecure HTTP protocol.

| Generation | Models | Protocol |
|---|---|---|
| Current | CP4-R V2, MC4-R, PC4-R | HTTPS |
| Previous | PYNG-HUB, CP3-R, CP4-R V1 | HTTP |

> **NOTE**: To determine whether a CP4-R is a V1 or V2 model, connect the control system to the text console in Crestron Toolbox software (or an SSH console), and then issue the `ver -v` command. The V1 model will show "CP4-R Cntrl Eng", while the V2 model will show "CP4-R (HW Ver 2) Cntrl Eng". For more information, refer to the [Crestron Toolbox help file](https://help.crestron.com/toolbox/).

When a client connects to a control system for the first time, it sends a self-signed certificate with a valid date on which the client can validate against the current date and trust the connection.

The self-signed certificate will be renewed by the control system on every restart cycle and is valid for 30 years from the date of creation.

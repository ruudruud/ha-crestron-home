# Exception Handling

When exceptions occur during request processing, the Crestron Home OS REST API responds with an HTTP error code alongside application-level error information. The system also logs exceptions to system logs with enhanced detail beyond what is returned to the client.

## Error Response Format

When an error occurs, the API returns a JSON response containing an error source code, a descriptive error message, and the API version.

Response Type: Application/JSON

```json
{
  "errorSource": 7007,
  "errorMessage": "Invalid request format.",
  "version": "[API Version]"
}
```

## Error Response Fields

| Field | Type | Description |
|-------|------|-------------|
| errorSource | integer | A numeric code identifying the source at which the error occurred (see error source codes below). |
| errorMessage | string | A generic message regarding the error. |
| version | string | The API version. |

## Error Source Codes

For comprehensive details about error sources and their corresponding messages, refer to the [JSON Payload Fields](json-payload-fields.md) documentation. The following error source codes are defined:

| Code | Description |
|------|-------------|
| 5001 | Session expired |
| 5002 | Authentication |
| 6001 | Rooms |
| 7000 | Unhandled |
| 7001 | Login |
| 7003 | Lights |
| 7004 | Shades |
| 7005 | Logout |
| 7006 | Scenes |
| 7007 | Thermostats |
| 7008 | Fan mode |
| 7009 | System mode |
| 8000 | Invalid data |
| 8001 | Devices |
| 8005 | Security devices |
| 8006 | Sensors |
| 8007 | Door locks |
| 8008 | Scheduler |
| 8009 | Setpoint |
| 8010 | Media rooms |

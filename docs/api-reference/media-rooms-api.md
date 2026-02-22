# Media Rooms API

> **Note:** The official Crestron documentation uses the term "Media Rooms" for this API (endpoint: `/cws/api/mediarooms`). The Devices API lists these as type "media Zone". The JSON Payload Fields documentation also references "Media Rooms" fields.

The Media Rooms API enables retrieval of media room information and status within the Crestron Home OS system, as well as control of media room functions such as power, volume, mute, and source selection.

## GET mediarooms

Retrieves all available media rooms and their current status.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/mediarooms

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
  "mediaRooms": [
    {
      "currentVolumeLevel": 0,
      "currentMuteState": "Unmuted",
      "currentPowerState": "Off",
      "availableProviders": [
        "ATC-Audionet Internet Radio",
        "ATC-Audionet SiriusXM",
        "ATC-Audionet Librivox Audiobooks",
        "ATC-Audionet Pandora",
        "TrackFm XM",
        "TrackAmFM AM",
        "TrackAmFM FM",
        "TrackAM AM",
        "TrackAM FM"
      ],
      "availableVolumeControls": [
        "discrete"
      ],
      "availableMuteControls": [
        "discrete"
      ],
      "id": 2,
      "name": "Gym",
      "roomId": 2
    },
    {
      "currentVolumeLevel": 5898,
      "currentMuteState": "Unmuted",
      "currentPowerState": "On",
      "currentProviderId": 1,
      "availableProviders": [
        "ATC-Audionet Internet Radio",
        "ATC-Audionet SiriusXM",
        "ATC-Audionet Librivox Audiobooks",
        "ATC-Audionet Pandora",
        "TrackFm XM",
        "TrackAmFM AM",
        "TrackAmFM FM",
        "TrackAM AM",
        "TrackAM FM"
      ],
      "availableVolumeControls": [
        "discrete"
      ],
      "availableMuteControls": [
        "discrete"
      ],
      "id": 1,
      "name": "Atrium",
      "roomId": 1
    },
    {
      "currentVolumeLevel": 0,
      "currentMuteState": "Unmuted",
      "currentPowerState": "Off",
      "availableProviders": [],
      "availableVolumeControls": [
        "none"
      ],
      "availableMuteControls": [
        "none"
      ],
      "id": 1001,
      "name": "Whole House",
      "roomId": 1001
    },
    {
      "currentVolumeLevel": 0,
      "currentMuteState": "Unmuted",
      "currentPowerState": "Off",
      "availableProviders": [
        "ATC-Audionet Internet Radio",
        "ATC-Audionet SiriusXM",
        "ATC-Audionet Librivox Audiobooks",
        "ATC-Audionet Pandora",
        "TrackFm XM",
        "TrackAmFM AM",
        "TrackAmFM FM",
        "TrackAM AM",
        "TrackAM FM"
      ],
      "availableVolumeControls": [
        "discrete"
      ],
      "availableMuteControls": [
        "discrete"
      ],
      "id": 5,
      "name": "Bedroom",
      "roomId": 5
    },
    {
      "currentVolumeLevel": 0,
      "currentMuteState": "Unmuted",
      "currentPowerState": "Off",
      "availableProviders": [
        "ATC-Audionet Internet Radio",
        "ATC-Audionet SiriusXM",
        "ATC-Audionet Librivox Audiobooks",
        "ATC-Audionet Pandora",
        "TrackFm XM",
        "TrackAmFM AM",
        "TrackAmFM FM",
        "TrackAM AM",
        "TrackAM FM"
      ],
      "availableVolumeControls": [
        "discrete"
      ],
      "availableMuteControls": [
        "discrete"
      ],
      "id": 4,
      "name": "Garage",
      "roomId": 4
    }
  ],
  "version": ""
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| mediaRooms | array | An array of media room objects in the system. |
| currentVolumeLevel | integer | The current volume level of the media device. |
| currentMuteState | string | The current mute state of the device ("Muted", "Unmuted"). |
| currentPowerState | string | The current power state of the device ("On", "Off"). |
| currentProviderId | integer | The source provider set on the media device (present when a source is active). |
| availableProviders | array of strings | A list of available media source providers in the media room. |
| availableVolumeControls | array of strings | The volume controls available in the media room (e.g., "discrete", "none"). |
| availableMuteControls | array of strings | The mute controls available in the media room (e.g., "discrete", "none"). |
| id | integer | The unique media room ID within the Crestron Home system. |
| name | string | The media room name. |
| roomId | integer | The unique ID of the room operating as the media room. |
| version | string | The API version. |

## GET mediarooms/{id}

Retrieves information for a specific media room by its unique identifier.

### Syntax

- HTTPS Method: GET
- Base URI: /cws/api/mediarooms/{id}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the media room in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response

Response Type: Application/JSON

```json
{
  "mediaRooms": [
    {
      "currentVolumeLevel": 0,
      "currentMuteState": "Unmuted",
      "currentPowerState": "Off",
      "availableProviders": [
        "ATC-Audionet Internet Radio",
        "ATC-Audionet SiriusXM",
        "ATC-Audionet Librivox Audiobooks",
        "ATC-Audionet Pandora",
        "TrackFm XM",
        "TrackAmFM AM",
        "TrackAmFM FM",
        "TrackAM AM",
        "TrackAM FM"
      ],
      "availableVolumeControls": [
        "discrete"
      ],
      "availableMuteControls": [
        "discrete"
      ],
      "id": 2,
      "name": "Gym",
      "roomId": 2
    }
  ],
  "version": ""
}
```

### Response Fields

Same as GET mediarooms response fields (see above), filtered to the requested media room.

## POST mediarooms/{id}/mute

Mutes a specific media room.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/mediarooms/{id}/mute

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the media room in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response (Success)

Response Type: Application/JSON

```json
{
  "status": "success",
  "version": "1.000.0001"
}
```

### Sample Response (Failure)

Response Type: Application/JSON

```json
{
  "status": "failure",
  "errorMessage": "Media room with Id [id] has not found in the system.",
  "version": "1.000.0001"
}
```

## POST mediarooms/{id}/unmute

Unmutes a specific media room.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/mediarooms/{id}/unmute

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the media room in the system. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response (Success)

Response Type: Application/JSON

```json
{
  "status": "success",
  "version": "1.000.0001"
}
```

### Sample Response (Failure)

Response Type: Application/JSON

```json
{
  "status": "failure",
  "errorMessage": "Media room with Id [id] has not found in the system.",
  "version": "1.000.0001"
}
```

## POST mediarooms/{id}/selectsource/{sid}

Selects the input source for a specific media room.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/mediarooms/{id}/selectsource/{sid}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the media room in the system. |
| {sid} | The unique identifier for the input source in the room. |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response (Success)

Response Type: Application/JSON

```json
{
  "status": "success",
  "version": "1.000.0001"
}
```

### Sample Response (Failure)

Response Type: Application/JSON

```json
{
  "status": "failure",
  "errorMessage": "Media room with Id [id] has not found in the system.",
  "version": "1.000.0001"
}
```

## POST mediarooms/{id}/volume/{level}

Sets the volume level for a specific media room.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/mediarooms/{id}/volume/{level}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the media room in the system. |
| {level} | The volume level to set (0-100 percent). |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response (Success)

Response Type: Application/JSON

```json
{
  "status": "success",
  "version": "1.000.0001"
}
```

### Sample Response (Failure)

Response Type: Application/JSON

```json
{
  "status": "failure",
  "errorMessage": "Media room with Id [id] has not found in the system.",
  "version": "1.000.0001"
}
```

## POST mediarooms/{id}/power/{state}

Controls the power state for a specific media room.

### Syntax

- HTTPS Method: POST
- Base URI: /cws/api/mediarooms/{id}/power/{state}

### Parameters

| Name | Description |
|------|-------------|
| {id} | The unique identifier for the media room in the system. |
| {state} | The power state to set. Valid values: "on", "off". |

### Request Header

| Name | Value |
|------|-------|
| Crestron-RestAPI-AuthKey | [Authentication Key] |

### Sample Response (Success)

Response Type: Application/JSON

```json
{
  "status": "success",
  "version": "1.000.0001"
}
```

### Sample Response (Failure)

Response Type: Application/JSON

```json
{
  "status": "failure",
  "errorMessage": "Media room with Id [id] has not found in the system.",
  "version": "1.000.0001"
}
```

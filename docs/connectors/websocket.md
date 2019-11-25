# Websocket connector

A connector to listen for messages using websockets.

## Configuration

```yaml
connectors:
  websocket:
    # optional
    bot-name: "mybot" # default "opsdroid"
    max-connections: 10 # default is 10 users can be connected at once
    connection-timeout: 10 # default 10 seconds before requested socket times out
```

## Usage

This connector is for use when developing applications which will send messages to opsdroid. Messages are sent back and forth using websockets to allow two way realtime conversation.

To connect to the websocket connector you must first request a room and then connect to it via websockets.

#### `[POST] http://host:port/connector/websocket`
Request a new websocket id. This method is used for rate limiting. If too many users are connected this message will return a `429` error code until some users disconnect or time out.

Response
```json
{
  "socket": "afbf858c-010d-11e7-abd2-d0a637e991d3"
}
```

#### `[WEBSOCKET] http://host:port/connector/websocket/{socket}`
The websocket end point to connect to. Messages are sent and received as text broadcasts in the socket.

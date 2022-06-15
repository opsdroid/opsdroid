# Websocket

A connector to listen for messages using websockets.

## Configuration

```yaml
connectors:
  websocket:
    # optional
    bot-name: "mybot" # default "opsdroid"
    max-connections: 10 # default is 10 users can be connected at once
    connection-timeout: 10 # default 10 seconds before requested socket times out
    token: "secret-token" # Used to validate request before assigning socket
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

If you provided a `token` in your configuration, opsdroid will check if the token provided in the configuration exists in the request header and if it matches, if it doesn't opsdroid will return a `403` Forbidden error.

#### `[WEBSOCKET] http://host:port/connector/websocket/{socket}`
The websocket end point to connect to. Messages are sent and received as text broadcasts in the socket.

You can send a single string to be parsed by opsdroid, but you can also send a json string payload containing the keys `message`, `user` and `socket`. These keys will then be passed to the `Message` event.

For example:

```python
import json
payload = json.dumps({"message": "hello, world", "user": "BobTheBuilder", "socket": "123"})

websocket_connection.send_str(payload)
```

This payload will create a `Message` event with the following attributes:

```python
message = Message(text="hello, world", user="BobTheBuilder", target="123")
```
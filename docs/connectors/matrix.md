# Matrix

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to receive and respond to messages in [Matrix](https://matrix.org/) rooms.

Maintained by [@SolarDrew](https://github.com/SolarDrew).

## Requirements

To use this connector you will need to have a Matrix account, and login using your Matrix username (mxid) and password.

## Configuration

```yaml
connectors:
  matrix:
    # Required
    mxid: "@username:matrix.org"
    password: "mypassword"
    # A dictionary of rooms to connect to
    # One of these have to be named 'main'
    rooms:
      'main': '#matrix:matrix.org'
      'other': '#riot:matrix.org'
    # Optional
    homeserver: "https://matrix.org"
    device_name: "opsdroid"
    nick: "Botty McBotface"  # The nick will be set on startup
    room_specific_nicks: False  # Look up room specific nicknames of senders (expensive in large rooms)
```

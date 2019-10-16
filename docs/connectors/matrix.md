# opsdroid connector Matrix

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to receive and respond to messages in [Matrix](https://matrix.org/) rooms. 

Maintained by [@SolarDrew](https://github.com/SolarDrew).

## Requirements

To use this connector you will need to have a Matrix account, and login using your Matrix username (mxid) and password.

## Configuration

```yaml
connectors:
  - name: matrix
    # Required
    mxid: "@username:matrix.org"
    password: "mypassword"
    # Name of a single room to connect to
    room: "#matrix:matrix.org"
    # Alternatively, a dictionary of multiple rooms
    # One of these should be named 'main'
    rooms:
      'main': '#matrix:matrix.org'
      'other': '#riot:matrix.org'
    # Optional
    homeserver: "https://matrix.org"
    nick: "Botty McBotface"  # The nick will be set on startup
    room_specific_nicks: False  # Look up room specific nicknames of senders (expensive in large rooms)
```

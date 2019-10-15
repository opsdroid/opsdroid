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
    # a dictionary of rooms to connect to, at least one is needed
    # # a dictionary of multiple rooms
    rooms:
      - '#matrix:matrix.org'
      - '#riot:matrix.org'
    # Optional
    homeserver: "https://matrix.org"
    nick: "Botty McBotface"  # The nick will be set on startup
    room_specific_nicks: False  # Look up room specific nicknames of senders (expensive in large rooms)
```

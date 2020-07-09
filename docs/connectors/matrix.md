# Matrix

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to receive and respond to messages in [Matrix](https://matrix.org/) rooms.

Maintained by [@SolarDrew](https://github.com/SolarDrew).

## Requirements

To use this connector you will need to have a Matrix account, and login using your Matrix username (mxid) and password.
The connector supports interacting with end to end encrypted rooms for which it will create a sqlite database to store the encryption keys into, this will be created in the store\_path.
Currently there is no device verification implemented which means messages will be sent regardless of whether encrypted rooms have users with unverified devices.

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
    nick: "Botty McBotface"  # The nick will be set on startup
    room_specific_nicks: False  # Look up room specific nicknames of senders (expensive in large rooms)
    device_name: "opsdroid"
    device_id: "opsdroid" # A unique string to use as an ID for a persistent opsdroid device
    store_path: "path/to/store/" # Path to the directory where the matrix store will be saved
```

# Matrix

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to receive and respond to messages in [Matrix](https://matrix.org/) rooms.

Maintained by [@SolarDrew](https://github.com/SolarDrew).

## Requirements

To use this connector you will need to have a Matrix account, and login using your Matrix username (mxid) and access token. You can find the access token in the **Advanced** section of the **Help & About** tab in the **Settings** of the official <Riot.im> web client.

## Configuration

```yaml
connectors:
  matrix:
    # Required
    credentials:
      'token': 'mytoken'  # Your matrix Access Token
      # Alternatively, you could use your matrix username and password (not recommended)
      'mxid' : '@username:matrix.org'
      'password': 'mypassword'
    # A dictionary of rooms to connect to
    # One of these have to be named 'main'
    rooms:
      'main': '#matrix:matrix.org'
      'other': '#riot:matrix.org'
    # Optional
    homeserver: "https://matrix.org"
    nick: "Botty McBotface"  # The nick will be set on startup
    room_specific_nicks: False  # Look up room specific nicknames of senders (expensive in large rooms)
```

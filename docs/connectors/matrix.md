# Matrix

A connector for [opsdroid](https://github.com/opsdroid/opsdroid) to receive and respond to messages in [Matrix](https://matrix.org/) rooms.

Maintained by [@SolarDrew](https://github.com/SolarDrew).

## Requirements

To use this connector you will need to have a Matrix account, and login using either your Matrix username (mxid) and password or your access token. You can find the access token in the **Advanced** section of the **Help & About** tab in the **Settings** of the official <Riot.im> web client. 
If your homeserver is matrix.org, the homeserver field is optional.

## Configuration

```yaml
connectors:
  matrix:
    # Required
    'mxid' : '@username:matrix.org'
    'password': 'mypassword'
    # Alternatively, you could use your matrix access token
    'token': 'mytoken'
    # A dictionary of multiple rooms
    # One of these should be named 'main'
    rooms:
      'main': '#matrix:matrix.org'
      'other': '#riot:matrix.org'
    homeserver: "https://matrix.org" # Optional if the homeserver is https://matrix.org
    # Optional
    nick: "Botty McBotface"  # The nick will be set on startup
    room_specific_nicks: False  # Look up room specific nicknames of senders (expensive in large rooms)
```

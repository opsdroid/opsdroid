# Rocket.Chat connector

A connector for [Rocket.Chat](https://rocket.chat).

## Requirements

 * An account from [Rocket.Chat](https://open.rocket.chat/home) chat service or from your own server
 * The Personal Access Token details(_user-id and token_) generated from within your account settings

## Configuration

```yaml
connectors:
  - name: rocketchat
    # required
    user-id: "1ioKHDIOD"
    token: "zyxw-abdcefghi-12345"
    # optional
    bot-name: "mybot" # default "opsdroid"
    default-room: "random" # default "general"
    group: "MyAwesomeGroup" # default to None 
    channel-url: "http://127.0.0.1" # defaults to https://open.rocket.chat
    update-interval: 5 # defaults to 1
```

_Notes:_

- The name of the channel room is meant to be added without the #.
- A group is a private channel - this takes priority over a channel when trying to connect to the service.
- Opsdroid will keep pinging the chat service to see if new messages where received, you can increase/decrease 
the time between pings by adding the param `update-interval`. _Note: Opsdroid will only read the last received message._



## Usage


```
FabioRosado Owner 6:11 PM
hi

opsdroid @FabioRosado Owner 6:11 PM
Hi FabioRosado
```

In this example, I was using my own account to interact with opsdroid through Rocket.Chat, so you can see that 
even thought opsdroid replied to "hi", the actual username shown was mine - this happens because I used my personal 
access token to test the connection. 

This will also give you the possibility to just use a single account and interact with opsdroid through the chat service
since the name will always be changed to whatever `bot-name` is set in `config.yaml`. 
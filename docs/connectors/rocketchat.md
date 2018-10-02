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
    group: "MyAwesomeGroup" # default to none 

```


## Usage


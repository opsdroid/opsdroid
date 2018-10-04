# Telegram connector

A connector for [Telegram](https://telegram.org/).

## Requirements

- An Telegram account - to create a bot
- An Bot API Token

_Note: To register a new bot, open Telegram, write **@BotFather** and type `/newbot`. 
Provide a name and username (ending in bot) and BotFather will give you your API Token._



## Configuration

```yaml
connectors:
  - name: telegram
    # required
    token: "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ-ZYXWVUT"  # Telegram bot token
    # optional
    update-interval: 0.5  # Interval between checking for messages
    default-user: user1  # Default user to send messages to (overrides default room in connector)
    whitelisted-users:  # List of users who can speak to the bot, if not set anyone can speak
      - user1
      - user2
```

## Usage

To talk with Opsdroid you will have to start a new private chat by searching for the name of your bot
in the search bar.

For example, if you named your bot: `MyAwesome_Bot` you can just search for that name and wait for the 
result to show up, then click on the name of your bot and a new chat window will start. You can know talk 
with your bot and give him commands.

_Note: To avoid unauthorized users to interact with your bot you should specify a list of whitelisted users
in your `config.yaml`._

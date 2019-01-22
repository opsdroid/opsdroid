# Telegram connector

A connector for [Telegram](https://telegram.org/).

## Requirements

- A Telegram account - to create a bot
- A Bot API Token

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
result to show up, then click on the name of your bot and a new chat window will start. You can now talk 
with your bot and give him commands.

_Note: To avoid unauthorized users to interact with your bot you should specify a list of whitelisted users
in your `config.yaml`._

```
[6:13:11 PM] Fabio:
hello

Unread messages
[6:13:12 PM] opsdroid:
Hi FabioRosado
```

**Warning**

You can send multiple private messages to opsdroid through Telegram, but if you don't have opsdroid running then
the next time you run opsdroid all those messages will be parsed by opsdroid resulting in a stream of replies.

```bash
[8:18:10 AM] Fabio:
bye
 hi
 hello
[8:18:10 AM] opsdroid:
Bye FabioRosado
 Hey FabioRosado
 Hi FabioRosado
```

To avoid this from happening, you should only contact the bot when opsdroid is running. The bot should reply immediately.
If it doesn't, check that the bot is running before attempting to send another command - or try with a risk free one like `hello`.
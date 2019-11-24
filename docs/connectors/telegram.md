# Telegram

A connector for [Telegram](https://telegram.org/).

## Requirements

- A Telegram account - to create a bot
- A Bot API Token

_Note: To register a new bot, open Telegram, write **@BotFather** and type `/newbot`.
Provide a name and username (ending in bot) and BotFather will give you your API Token._

## Configuration

```yaml
connectors:
  telegram:
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
in the search bar. The telegram API doesn't include the name of a user when they send a message to a channel,
so the connector is unable to trigger any commands sent from a channel.

For example, if you named your bot: `MyAwesome_Bot` you can just search for that name and wait for the result to show up, then click on the name of your bot and a new chat window will start. You can now talk with your bot and give him commands.


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
If it doesn't, check that the bot is running before attempting to send another command - or try with a risk-free one like `hello`.

## White listing users

This is an optional config option that you can include on your `config.yaml` to prevent unauthorized users to interact with your bot.
Currently, you can specify a user `nickname` or a `userID`. Using the `userID` method is preferable as it will increase the security
of the connector since users can't change this ID.

Here is how you can whitelist a user:

```yaml
  - name: Telegram
    token: <your bot token>
    whitelisted-users:
      - user1
      - 124324234 # this is a userID
```

Finding your `userID` is not straight forward. This value is sent by Telegram when a user sends a private message to someone (the bot in this case) or when someone calls the `getUpdate` from the API.
To find a `userID` by a private message, set the `logging` level to `debug` and start a new private message to the bot. You will see the API response on your console - it will look similar to this:

```json
{
   "update_id": 539026743,
   "message": {
      "message_id": 109,
      "from": {
         "id": 4532189818,
         "is_bot": false,
         "first_name": "user",
         "language_code": "en"
      },
      "chat": {}
   }
}
```

Use the `id` value from the `message["from"]` field and add it to your `whitelisted-users` config option.

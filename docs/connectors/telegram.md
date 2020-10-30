# Telegram

A connector for [Telegram](https://telegram.org/).

## Requirements

- A Telegram account - to create a bot
- A Bot API Token
- A secure url where opsdroid is running (could be forwarded by ngrok)

_Note: To register a new bot, open Telegram, write **@BotFather** and type `/newbot`.
Provide a name and username (ending in bot) and BotFather will give you your API Token._

## Configuration

```yaml
web:
  base-url: <https://your-opsdroid-url-or-ngrok-url>

connectors:
  telegram:
    # required
    token: "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ-ZYXWVUT"  # Telegram bot token
    # optional
    bot-name: opsdroid # Name to be used by the bot in some replies, defaults to opsdroid
    reply-unauthorized: false # Should the bot reply to unauthorized users?
    whitelisted-users:  # List of users who can speak to the bot, if not set anyone can speak
      - user1
      - user2
```

_**Note:** You MUST specify the `base-url` in the `web` config, otherwise opsdroid won't be able to receive webhook notifications._

## Usage


You can add this connector to:

- Direct Messages
- Groups
- Channels

If you want opsdroid to work on your group or channel, you should add it by opening your channel/group details and select the _Add Members_ button, then search for your bot username and add it. It's a good idea to add the bot as admin, because in some cases where you have privacy active, opsdroid won't be able to read user's names.

### Direct Messages

To interact with your bot directly, start a new message, click _search_ and type your bot name. For example, if you named your bot: `MyAwesome_Bot` you can just search for that name and wait for the result to show up, then click on the name of your bot and a new chat window will start. You can now talk with your bot and give him commands.


```
[6:13:11 PM] Fabio:
hello

Unread messages
[6:13:12 PM] opsdroid:
Hi FabioRosado
```

### Groups

Opsdroid will listen to every message sent to a group, so it's a good idea to set a list of users that can interact with the bot if you are using opsdroid skills that some users shouldn't be able to trigger.

To set up a list of users that can interact with the bot, you can set the option configuration parameter `whitelisted-users` - you should try to use the user `id` obtained from Telegram response. Also, you might want to set the configuration parameter `reply-unauthorized` to `false` so the bot doesn't send a message every time someone says something to the group.


### Channels

By default Telegram doesn't show the name of the user that sends messages to a channel, if you want to change this behaviour, you can open your channel, click the channel name to open the settings, chose _edit_ and toggle the option `Sign Messages`.

_**Note:** If you have a discussion group, opsdroid will reply to any command sent to a channel in that group._

## White listing users

This is an optional config option that you can include on your `config.yaml` to prevent unauthorized users to interact with your bot.
Currently, you can specify a user `nickname` or a `userID`. Using the `userID` method is preferable as it will increase the security of the connector since users can't change this ID.

Here is how you can whitelist a user:

```yaml
  telegram:
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

_**Note:** If you have the bot working in a group, you will want to set the config parameter `reply-unauthorized` to false, to prevent the bot to trigger with each message and spam your group._

## Parsing images/videos/files

Unfortunately we are unable to parse any of these formats, the reason for that is because Telegram doesn't send us any real useful information that we can feed to opsdroid. When you send an image to a channel, Telegram send us a file id, format and sizes, but no url or anything that we could use to download the image.

## Events Available

The Telegram Connector contains a few events that you can access on your skills. These events were created to allow you to use these messages types on your custom made skills.

```eval_rst
.. autoclass:: opsdroid.connector.telegram.events.Poll
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.telegram.events.Contact
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.telegram.events.Location
    :members:
```

```eval_rst
.. autoclass:: opsdroid.events.JoinGroup
    :members:
```

```eval_rst
.. autoclass:: opsdroid.events.LeaveGroup
    :members:
```

```eval_rst
.. autoclass:: opsdroid.events.PinMessage
    :members:
```

```eval_rst
.. autoclass:: opsdroid.events.Reply
    :members:
```

```eval_rst
.. autoclass:: opsdroid.events.EditedMessage
    :members:
```


## Reference

```eval_rst
.. autoclass:: opsdroid.connector.Telegram.ConnectorTelegram
 :members:
```


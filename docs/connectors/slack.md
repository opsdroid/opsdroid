# Slack connector

A connector for [Slack](https://slack.com/).

## Requirements

* A Slack account
* A [Slack App bot token](https://api.slack.com/bot-users).
  * Create a [new Slack App](https://api.slack.com/apps/new) and select the workspace you would like it in.
  * Navigate to the "Bot Users" section and add a bot, giving it a display name and username.
  * Navigate to the "Install App" section and install the app in your workspace.
  * Take note of the "Bot User OAuth Access Token" as this will be the `token` you need for your configuration.

## Configuration

```yaml
connectors:
  slack:
    # required
    token: "zyxw-abdcefghi-12345"
    # optional
    bot-name: "mybot" # default "opsdroid"
    default-room: "#random" # default "#general"
    icon-emoji: ":smile:" # default ":robot_face:"
    connect-timeout: 10 # default 10 seconds
    chat-as-user: true # default false
```

## Usage
The connector itself won't allow opsdroid to do much. It will connect to Slack and be active on the `default-room`
but you will still need some skill to have opsdroid react to an input.

Luckily, opsdroid comes with few skills out of the box as well. So once you run opsdroid you will see that it joined either the room that you set up on `default-room` parameter in the configuration or it will be in the `#general` room.

_Note: If opsdroid failed to join the room you can always invite him by clicking `info>Members section>invite more people...`_

You can also interact with opsdroid through direct message. To do so, just click on opsdroid's name and type something on the box that says "Message opsdroid".

Example of a private message:

```
fabiorosado [7:06 PM]
hi

opsdroid APP [7:06 PM]
Hi fabiorosado
```

## Rich layouts and blocks

Slack has support for [rich layouts](https://api.slack.com/messaging/composing/layouts) using a concept they call [blocks](https://api.slack.com/reference/messaging/blocks). Blocks are JSON objects which describe a rich element, and a list of them can be passed instead of a message to produce rich content.

To do this you need to respond with an `opsdroid.connector.slack.events.Blocks` event which is constructed with a list of blocks.

### Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
from opsdroid.connector.slack.events import Blocks


class BlocksSkill(Skill):

    @match_regex(r"who are you\?")
    async def who_are_you(self, event):
        await event.respond(Blocks([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Hey! I'm opsdroid.\nI'm a natural language event driven automation bot framework.\n*What a mouthful!*"
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": "https://raw.githubusercontent.com/opsdroid/style-guidelines/master/logos/logo-light.png",
                        "alt_text": "opsdroid logo"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Visit website",
                                "emoji": True
                            },
                            "url": "https://opsdroid.dev"
                        }
                    ]
                }
            ]
        ))

```

![](https://user-images.githubusercontent.com/1610850/58658951-ac523300-8319-11e9-8c2a-011469a436d0.png)

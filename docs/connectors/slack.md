# Slack

A connector for [Slack](https://slack.com/).

## Requirements

* A Slack account
* Create a [new classic Slack App](https://api.slack.com/apps?new_classic_app=1) give it a name and select the workspace you would like it in.
  * Select `Bots` option inside the `Add features and functionality` tab
  * Click Add Legacy Bot User and give it a name and a username
  * Navigate to the "Install App" section and install the app in your workspace.
  * Take note of the "Bot User OAuth Access Token" as this will be the `token` you need for your configuration (the token will start with `xoxb-`).

## Configuration

```yaml
connectors:
  slack:
    # required
    token: "xoxb-abdcefghi-12345"
    # optional
    bot-name: "mybot" # default "opsdroid"
    default-room: "#random" # default "#general"
    icon-emoji: ":smile:" # default ":robot_face:"
    connect-timeout: 10 # default 10 seconds
    chat-as-user: true # default false
    start_thread: false # default false. if true, opsdroid will start a thread when replying to a message
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

### Send Block

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

### Edit an existing Block

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
from opsdroid.connector.slack.events import EditedBlocks


class UpdateBlocksSkill(Skill):

    @match_regex(r"edit block with ts 1605646357.261200")
    async def who_are_you(self, event):
    	# linked_event == the timestamp of the block to edit
    	# target == channel id
	blocks = ["the blocks datastructure"]
        await self.opsdroid.send(EditedBlocks(blocks, linked_event=1605646357.261200, target="channel_id"))
```

## Interactive Actions

Slack apps can use [interactive features](https://api.slack.com/interactivity) to achieve much more than just one-way communication. Apps can implement a number of interaction entry points that allow users to intentionally invoke a response from the app.

When one of those entry points is triggered, a new aspect is introduced to the [interaction transaction](https://api.slack.com/interactivity/handling) — the interaction payload. This payload is a bundle of information that explains the context of the user action, giving the app enough to construct a coherent response.

For example, when you click a button in a rich Slack message or use a message action (a todo list app may have an "add to list" action that can be performed on any message) Slack will send an event to a separate webhook endpoint.

### Configure Slack App for Interactive Events

- Open your app's [management dashboard](https://api.slack.com/apps)
- Click on `Interactive Components` in the sidebar.
- Toggle the `Interactivity` switch on.
- Save the HTTPS URL of your bot's slack interactivity endpoint (`/connector/slack/interactions`).
    - *Example:* `https://slackbot.example.com/connector/slack/interactions`

### [block_actions](https://api.slack.com/reference/interaction-payloads/block-actions)

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_event
from opsdroid.connector.slack.events import BlockActions

class InteractionsSkill(Skill):

    @match_event(BlockActions, value="click_me_123")
    async def slack_interactions(self, event):
        await event.respond("Block Actions interactivity has been triggered.")
```

### [message_action](https://api.slack.com/reference/interaction-payloads/actions)

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_event
from opsdroid.connector.slack.events import MessageAction

class InteractionsSkill(Skill):

    @match_event(MessageAction)
    async def slack_interactions(self, event):
        await event.respond("Message Action interactivity has been triggered.")
```

### [view_submission](https://api.slack.com/reference/interaction-payloads/views#view_submission)

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_event
from opsdroid.connector.slack.events import ViewSubmission

class InteractionsSkill(Skill):

    @match_event(ViewSubmission)
    async def slack_interactions(self, event):
        await self.opsdroid.send(Message("View Submission interactivity has been triggered."))
```

### [view_closed](https://api.slack.com/reference/interaction-payloads/views#view_closed)

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_event
from opsdroid.connector.slack.events import ViewClosed

class InteractionsSkill(Skill):

    @match_event(ViewClosed)
    async def slack_interactions(self, event):
        await self.opsdroid.send(Message("View Closed interactivity has been triggered."))
```

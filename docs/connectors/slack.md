# Slack

A connector for [Slack](https://slack.com/).

## ⚠️ **Breaking Changes introduced in opsdroid 0.21.0**

We have dropped support for the RTM API. Now the Slack Connector uses the [events API](https://api.slack.com/apis/connections/events-api) and [Socket Mode](https://api.slack.com/apis/connections/socket)

### Migrating away from RTM
* Follow Requirements and Configuration steps and choose the *Socket Mode* Backend.

## Requirements

* A Slack account
* Create a [new Slack App](https://api.slack.com/apps) give it a name and select the workspace you would like it in.
* Select "Bots" option inside the "Add features and functionality" tab
* Click "Review Scopes to Add". "Under Scopes" --> "Bot Token Scopes select" `chat:write` or `chat:write.customize` (Note that you are required to select at least one scope to install the app)
* Navigate to "OAuth Tokens & Redirect URLs" and click the "Install to Workspace" button. 
* Take note of the "Bot User OAuth Access Token" as this will be the `token` you need for your configuration (the token will start with `xoxb-`).


## Configuration

```yaml
connectors:
  slack:
    # required
    token: "xoxb-abdcefghi-12345"
    # optional
    socket-mode: True # defaul false. if true app-token is required
    app-token: "xapp-abdcfkje-12345" # socket-mode needs to be true
    bot-name: "mybot" # default "opsdroid" **
    icon-emoji: ":smile:" # default ":robot_face:" **
    default-room: "#random" # default "#general"
    start_thread: false # default false. if true, opsdroid will start a thread when replying to a message
```

** In order for `bot-name` and/or `icon-emoji` to work, the `chat:write.customize` scope will have to be selected

### Choose the Backend API

You need to choose between two backends. The [Events API](https://api.slack.com/apis/connections/events-api) or [Socket Mode](https://api.slack.com/apis/connections/socket).

If you are unsure which one is the best for you, [Slack Faq](https://api.slack.com/faq#events_api) provide differences between those two.

**Events API**

* You will need an **endpoint** which exposes your Opsdroid to the **internet**. [Exposing Opsdroid via tunnels](https://docs.opsdroid.dev/en/latest/exposing.html) might help out.
* Go to your [Slack App](https://api.slack.com/apps)
* On the left column go to "Event Subscriptions" and toogle the "Enable Events"
* Under "Request URL" add the `/connector/slack` uri to your endpoint: https://slackbot.example.com/connector/slack. Note that you will have to have your Opsdroid instance running so Slack can validate the endpoint.
For Socket Mode, you will nee 

**Socket Mode**
* Go to your [Slack App](https://api.slack.com/apps)
* On the left columnt go to "Socket Mode" and toogle the "Enable Socket Mode"
* Copy your new token add add it to your opsdroid configuration file as your `app-token`. Make sure also to set `socket-mode` to `True`


### Subscribe to events
You will need to subscribe to events in your new Slack App, so Opsdroid can receive those events.
* Under "Subscribe to bot events" choose the events you want to subscribe for. You need at least one, `message.channels` will allow you to receive events everytime a message is posted into a channel. The following events are also supported by opsdroid: `message.im`, `channel_archive`, `channel_unarchive`, `channel_created`, `channel_rename`, `pin_added`, `pin_removed` and `team_join`.
* Don't forget to save your changes in the slack app.
 
## Usage
The connector itself won't allow opsdroid to do much. It will connect to Slack and be active on the `default-room`
but you will still need some skill to have opsdroid react to an input.

Luckily, opsdroid comes with few skills out of the box as well. So once you run opsdroid you will see that it joined either the room that you set up on `default-room` parameter in the configuration or it will be in the `#general` room.

_Note: If opsdroid failed to join the room you can always invite him by clicking "Channel Details" -> "Add Apps"_

You can also interact with opsdroid through direct message (make sure to be subscribed to the `message.im` event). To do so, just click on opsdroid's name and type interact like with any other user

Below is an example of a simple skill you can use to create your opsdroid. Checkout [Skill](https://docs.opsdroid.dev/en/stable/skills) for more info

***Sample Greeter Skill***
```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class GreeterSkill(Skill):
    """This is the most simple form of a skill, keeping it for pinging purposes"""

    @match_regex(r"Hi Opsdroid")
    async def hello(self, message):
        """Respond Hi"""
        await message.respond("Hi")
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
- Save the HTTPS URL of your bot's slack interactivity endpoint (`/connector/slack`).
    - *Example:* `https://slackbot.example.com/connector/slack`

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

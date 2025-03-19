# Slack

A connector for [Slack](https://slack.com/).

- [Requirements](#requirements)
- [Configuration](#slack-configuration)
    - [Choose the backend API](#choose-the-backend-api)
    - [Subscribe to events](#subscribe-to-events)
- [Usage](#usage)
    - [Basic Skill Example](#basic-skill-example)
    - [Get Messages from History](#get-messages-from-history)
    - [Find channel by name](#find-channel-by-name)
    - [Rich layouts and blocks](#rich-layouts-and-blocks)
    - [Slash Commands](#slash-commands)
    - [Modals](#modals)
    - [Interactive Actions](#interactive-actions)
    - [Matching Events in Interactive Actions](#matching-events-in-interactive-actions)


## ⚠️ **Breaking Changes introduced in opsdroid 0.22.0**

We have dropped support for the RTM API. Now the Slack Connector supports the [events API](https://api.slack.com/apis/connections/events-api) and [Socket Mode](https://api.slack.com/apis/connections/socket) from new apps

### Migrating away from RTM
* Follow Requirements and Configuration steps and choose the *Socket Mode* Backend.
(requirements)=
## Requirements

* A Slack account
* Create a [new Slack App](https://api.slack.com/apps) --> "From scratch" and give it a name and select the workspace you would like it in.
* Inside the "Add features and functionality" tab select "Bots" option 
* Click "Review Scopes to Add". Under "Scopes" --> "Bot Token Scopes" select "Add an OAuth Scope" and choose `users:read` **and** `chat:write` (+`chat:write.customize` if you want to send messages as @your_slack_app with a customized username and avatar)

  >Note that you are required to select at least one scope to install the app
* Navigate to "OAuth Tokens for your Workspace" and click the "Install to Workspace" button. 
* Take note of the "Bot User OAuth Access Token" as this will be the `bot-token` you need for your configuration (the bot-token will start with `xoxb-`).

(slack-configuration)=
## Configuration

```yaml
connectors:
  slack:
    # required
    bot-token: "xoxb-abdcefghi-12345"

    # Optional

    # when socket-mode is true, you need to set also an `app-token`
    # more info: https://api.slack.com/authentication/token-types#app
    socket-mode: true # defaul true.
    # socket-mode needs to be set to true to use app-token
    app-token: "xapp-abdcfkje-12345"

    # In order for bot-name and/or icon-emoji to work, the `chat:write.customize`
    # scope will have to be selected
    bot-name: "mybot" # default "opsdroid"
    icon-emoji: ":smile:" # default ":robot_face:"

    default-room: "#random" # default "#general"

    # If set to true opsdroid will start a thread when replying to a message
    start-thread: false # default false

    # Used to retrieve the conversations details from Slack API
    # refresh-interval: how often the connector will refresh the channels
    refresh-interval: 600 # default 600
    # channel-limit: Maximum channels to return on a single iteration.
    # if your instance has >1000 channels, consider raising this
    # (https://api.slack.com/methods/conversations.list#arg_limit)
    channel-limit: 100 # default 100. ***
```
(choose-the-backend-api)=
### Choose the Backend API

You need to choose between two backends. The [Events API](https://api.slack.com/apis/connections/events-api) or [Socket Mode](https://api.slack.com/apis/connections/socket).

If you are unsure which one is the best for you, [Slack Faq](https://api.slack.com/faq#events_api) provide differences between those two.

```{note}
While it is not mandatory to configure the Event API before using Slack in Socket Mode, we recommend
setting up the Event API for its full feature set.
```

**1. Events API**

* Make sure to set `socket-mode` to `false` in your Opsdroid configuration.
* You will need an **endpoint** which exposes your Opsdroid to the **internet**. [Exposing Opsdroid via tunnels](https://docs.opsdroid.dev/en/latest/exposing.html) might help out.
* Go to your [Slack App](https://api.slack.com/apps)
* On the left column go to "Socket Mode" and make sure the "Enable Socket Mode" toggle is set to disabled.
* On the left column go to "Event Subscriptions" and set the "Enable Events" toggle to enabled.
* Under "Request URL" add the `/connector/slack` uri to your endpoint: https://slackbot.example.com/connector/slack. Note that you will have to have your Opsdroid instance running so Slack can verify the endpoint.

**2. Socket Mode**
* Go to your [Slack App](https://api.slack.com/apps)
* On the left column go to "Socket Mode", set the "Enable Socket Mode" toggle to enabled and give your token a name.
* Copy your token add add it to your Opsdroid configuration file as your `app-token`. (the `app-token` will start with `xapp-abcdef-1233`)
* Make sure to set `socket-mode` to `true` in your Opsdroid configuration.


(subscribe-to-events)=
### Subscribe to events
You will need to subscribe to events in your new Slack App, so Opsdroid can receive those events.
You need to subscribe to events regardless of the backend: **Socket Mode** or **Events API**
* On the left column go to "Event Subscriptions" and set the "Enable Events" toggle to enabled.
* Under "Subscribe to bot events" choose the events you want to subscribe for. You need at least one, `message.channels` will allow you to receive events everytime a message is posted into a channel. The following events are also supported by opsdroid: `message.im`, `channel_archive`, `channel_unarchive`, `channel_created`, `channel_rename`, `pin_added`, `pin_removed` and `team_join`.
* Don't forget to save your changes in the slack app and reinstall your app.
(usage)= 
## Usage
The connector itself won't allow opsdroid to do much. It will connect to Slack and be active on the `default-room`
but you will still need some skill to have opsdroid react to an input.

Luckily, opsdroid comes with few skills out of the box as well.([dance()](https://github.com/opsdroid/skill-dance), [hello()](https://github.com/opsdroid/skill-hello), [loudnoises()](https://github.com/opsdroid/skill-loudnoises), [seen()](https://github.com/opsdroid/skill-seen)) So once you run opsdroid on your CLI you will see that it joined either the room that you set up on `default-room` parameter in the configuration or it will be in the `#general` room.

_Note: If opsdroid failed to join the room you can always invite him by clicking "Channel Details" -> "Add Apps"_

You can also interact with opsdroid through direct message (make sure to be subscribed to the `message.im` event). To do so, just click on opsdroid's name and type interact like with any other user

Below is an example of a simple skill you can use to create your opsdroid. Checkout [Skill](../skills/index.md) for more info
(basic-skill-example)=
### Basic Skill Example
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
(get-messages-from-history)=
### Get Messages from History
Sometimes you need to search through the history of a channel. For this you can use the `search_history_messages` method from the slack connector which returns all the messages on a specified range of time.

```{autofunction} opsdroid.connector.slack.ConnectorSlack.search_history_messages
```
(find-channel-by-name)=
### Find channel by name
Sometimes you need to find the channel details (ie: id, purpose). For this you can use the `find_channel` method from the slack connector which returns the details of the channel

```{autofunction} opsdroid.connector.slack.ConnectorSlack.find_channel
```
(rich-layouts-and-blocks)=
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
(slash-commands)=
## Slash Commands
[Slash Commands](https://api.slack.com/interactivity/slash-commands) allow users to invoke opsdroid by typing a string into the message composer box.

### Configure Slack App for Slash Commands
- Open your app's [management dashboard](https://api.slack.com/apps)
- Click on `Slash Commands` in the sidebar.
- Click the `Create New Command` button
- If you are using the events API, save the HTTPS URL of your bot's slack connector entpoint (`/connector/slack`).
    - *Example:* `https://slackbot.example.com/connector/slack`

### Slash Command
```{autofunction} opsdroid.connector.slack.events.SlashCommand
```
(modals)=
## Modals
[Modals](https://api.slack.com/surfaces/modals/using) provide focused spaces ideal for requesting and collecting data from users, or temporarily displaying dynamic and interactive information.

### Modal Usage Example
```{autofunction} opsdroid.connector.slack.events.ModalOpen
```
(interactive-actions)=
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

(block_actions)=
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
(matching-events-in-interactive-actions)=
## Matching events in Interactive Actions

In the [block_actions](#block_actions) example above, you can also match on `action_id` and/or `block_id` in addition to `value` for `match_event` like any of these:

```python
    @match_event(BlockActions, action_id="text1234")
    @match_event(BlockActions, action_id="text1234", value="click_me_123")
    @match_event(BlockActions, block_id="section678")
    @match_event(BlockActions, block_id="section678", value="click_me_123")
    @match_event(BlockActions, block_id="section678", action_id="text1234", value="click_me_123")
```

# Twitch

A connector for [Twitch](https://twitch.tv/).

## Requirements

- A Twitch Account
- A Twitch App obtained from [Twitch developers page](https://dev.twitch.tv/console/apps)
- The `code` obtained from the first step of OAuth

## Configuration

```yaml
connectors:
  twitch:
    # required
    code: "hfu923hfks02nd2821jfislf" # Code obtained from the first OAuth step
    client-id: "e0asdj48jfkspod0284"
    client-secret: "kdksd0458j93847j"
    channel: theflyingdev # Broadcaster channel
    redirect: http://localhost # Url to be passed to get oath token - defaults to localhost
    forward-url: 'http://94jfsd9ff.ngrok.io' # Either an URL provided by a forwarding service or an exposed ip address
    # optional
    webhook-lease-seconds: 86400 # how long for webhooks to expire
    always-listening: false # Turn on to connect to the chat server even if stream is offline.
```

## Setup Twitch App

You need to create a [Twitch App](https://dev.twitch.tv/console/apps) to use the Twitch Connector. Click the `+ Register Your Application` button, give this app a name and a redirect url - using `http://localhost` is fine. Once created, you can click the `Manage` button and get your `client-id`, you can then get a `client-secret` by pressing the `New Secret` button (keep this secret safe as it won't be shown to you again).

## Getting OAuth code

Twitch OAuth has two steps, first you need to make a `GET` request to a specific URL to obtain a `code`. After you've received the code, you need to make a `POST` request to the same URL and Twitch will send you an `access_token` and `refresh_token`. 

After a certain period, the `access_token` will expire and you have to make a new request with your `refresh_token` to re-authenticate yourself. 

_NOTE: The Twitch Connector will handle token expiration and re-authentication for you._

### Step 1 - Getting Code

To get your code, you need to make a request to `https://id.twitch.tv/oauth2/authorize` with the following parameters:

- client_id
- redirect_uri
- response_type
- scope

Both the `client_id` and `redirect_uri` can be obtained when you click the `Manage` button on your app. The `response_type` that we want will be `code` and we will ask for a lot of scopes. You can check the [API Scopes](https://dev.twitch.tv/docs/v5/guides/migration#scopes) and the [IRC Scopes](https://dev.twitch.tv/docs/irc/guide#scopes-for-irc-commands) to read more about what we are asking and why.

The Twitch Connector interacts with a wide range of services - IRC server, New API, V5 API - so we need to pass a big number of scopes to make sure everything works as expected.

#### Recommended scopes

```
channel:read:subscriptions+channel_subscriptions+analytics:read:games+chat:read+chat:edit+viewing_activity_read+channel_feed_read+channel_editor+channel:read:subscriptions+user:read:broadcast+user:edit:broadcast+user:edit:follows+channel:moderate+channel_read
```

#### Example: OAuth URL

You can use this example url to make your request - make sure you add your `client_id` before making the request. After adding your client id, you can open the url on a browser window, accept the request and Twitch will send you back to your `redirect_url`. Look at the address bar and you will see that it contains a `code=jfsd98hjh8d7da983j` this is what you need to add to your opsdroid config.

```
https://id.twitch.tv/oauth2/authorize?client_id=<your client id>&redirect_uri=http://localhost&response_type=code&scope=channel:read:subscriptions+channel_subscriptions+analytics:read:games+chat:read+chat:edit+viewing_activity_read+channel_feed_read+channel_editor+channel:read:subscriptions+user:read:broadcast+user:edit:broadcast+user:edit:follows+channel:moderate+channel_read
```

## Usage

The connector will subscribe to followers alerts, stream status (live/offline) and subscriber alerts, it will also connect to the chat service whenever the stream status notification is triggered and the `StreamStarted` event is triggered by opsdroid. If you wish you can set the optional config parameter `always-listening: True` to connect to the chat whenever opsdroid is started.

### Events Available

The Twitch Connector contains 10 events that you can use on your custom made skill. Some of these events are triggered automatically whenever an action happens on twitch - for example when a user follows your channel. Others you will have to trigger on a skill - for example, to delete a specific message.

#### Automatic Events

These events are triggered by opsdroid whenever something happens on twitch.

```eval_rst
.. autoclass:: opsdroid.events.JoinRoom
    :members:
```

```eval_rst
.. autoclass:: opsdroid.events.LeaveRoom
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.twitch.events.UserFollowed
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.twitch.events.UserSubscribed
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.twitch.events.UserGiftedSubscription
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.twitch.events.StreamStarted
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.twitch.events.StreamEnded
    :members:
```

#### Manual Events

These events will have to be triggered by you with an opsdroid skill.

```eval_rst
.. autoclass:: opsdroid.connector.twitch.events.UpdateTitle
    :members:
```

```eval_rst
.. autoclass:: opsdroid.connector.twitch.events.CreateClip
    :members:
```

```eval_rst
.. autoclass:: opsdroid.events.DeleteMessage
    :members:
```

```eval_rst
.. autoclass:: opsdroid.events.BanUser
    :members:
```

## Examples

You can write your custom skills to interact with the Twitch connector, here are a few examples of what you can do. You can also use the [Twitch Skill](https://github.com/FabioRosado/skill-twitch) to interact with the connector.

### StreamStarted event

Let's say that you want to send a message to another connector whenever you go live, you can achieve this by writing that will be triggered when the **StreamStarted** event is triggered.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_event
from opsdroid.connector.twitch.events import StreamStarted


class TwitchSkill(Skill):
 """opsdroid skill for Twitch."""
    def __init__(self, opsdroid, config, *args, **kwargs):
        super().__init__(opsdroid, config, *args, **kwargs)
        self.rocketchat_connector = self.opsdroid.get_connector('rocketchat')

    @match_event(StreamStarted)
    async def stream_started_skill(event):
    """Send message to rocketchat channel."""
        await self.rocketchat_connector.send(Message(f"I'm live on twitch, come see me work on {event.title}"))

```


### UserFollowed event

Some bots will send a thank you message to the chat whenever a user follows your channel. You can do the same with opsdroid by using the **UserFollowed** event.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_event
from opsdroid.connector.twitch.events import UserFollowed


class TwitchSkill(Skill):
 """opsdroid skill for Twitch."""
    def __init__(self, opsdroid, config, *args, **kwargs):
        super().__init__(opsdroid, config, *args, **kwargs)
        self.connector = self.opsdroid.get_connector('twitch')

    @match_event(UserFollowed)
    async def say_thank_you(event):
    """Send message to rocketchat channel."""
        await self.connector.send(Message(f"Thank you so much for the follow {event.follower}, you are awesome!"))

```

### BanUser event

We have seen how to send messages to the chat, how about we remove a spam message and ban bots from trying to sell you followers, subs and viewers?

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
from opsdroid.connector.twitch.events import BanUser, DeleteMessage


class TwitchSkill(Skill):
 """opsdroid skill for Twitch."""
    def __init__(self, opsdroid, config, *args, **kwargs):
        super().__init__(opsdroid, config, *args, **kwargs)
        self.connector = self.opsdroid.get_connector('twitch')

    @match_regex(r'famous\? Buy followers', case_sensitive=False)
    async def goodbye_spam_bot(self, message):
        await self.connector.send(BanUser(user=message.user))
        deletion = DeleteMessage(id=message.event_id)
        await self.connector.send(deletion)
```

### UpdateTitle event

You need to be careful on how you set this skill, you should have a list of users that are allowed to change your broadcast title otherwise it can be abused while you are streaming. 

```python
from opsdroid.skill import Skill
from opsdroid.constraints import constrain_users
from opsdroid.matchers import match_regex
from opsdroid.connector.twitch.events import UpdateTitle


class TwitchSkill(Skill):
 """opsdroid skill for Twitch."""
    def __init__(self, opsdroid, config, *args, **kwargs):
        super().__init__(opsdroid, config, *args, **kwargs)
        self.connector = self.opsdroid.get_connector('twitch')

    @match_regex(r'\!title (.*)')
    @constrain_users(your_awesome_twitch_username)
    async def change_title(self, message):
        _LOGGER.info("Attempt to change title")
        await self.connector.send(UpdateTitle(status=message.regex.group(1)))
```

You could also add a `whitelisted` config param to your skill and then read the configuration to check if the user that tried to change the title is in that list.

```yaml
skills:
  - twitch:
    whitelisted: 
      - your_username_on_twitch
      - your_username_on_another_connector
```

```python
from opsdroid.skill import Skill
from opsdroid.constraints import constrain_users
from opsdroid.matchers import match_regex
from opsdroid.connector.twitch.events import UpdateTitle


class TwitchSkill(Skill):
 """opsdroid skill for Twitch."""
    def __init__(self, opsdroid, config, *args, **kwargs):
        super().__init__(opsdroid, config, *args, **kwargs)
        self.connector = self.opsdroid.get_connector('twitch')

    @match_regex(r'\!title (.*)')
    async def change_title(self, message):
        if message.user in self.config.get('whitelisted', []):
        await self.connector.send(UpdateTitle(status=message.regex.group(1)))
```


## Reference

```eval_rst
.. autoclass:: opsdroid.connector.twitch.ConnectorTwitch
 :members:
```

# Mastodon

Connector for [Mastodon](https://mastodon.social/about).

## Requirements

To use the Mastodon connector you will need a user for the bot to use and generate an application access token.
Not all servers are friendly to bot users to be sure to check the local rules, check out [botsin.space](https://botsin.space) which is specifically for bot users.

### Creating your application

- Create a new Mastodon user on your desired server
- Create a new application on the `https://<server>/settings/applications` page
- Take note of "your access token"

## Configuration

```yaml
connectors:
  mastodon:
    # Required
    access-token: "abc123"  # Your access token
    api-base-url: https://botsin.space/  # The domain of your Mastodon server
```

## Supported actions

Right now only sending toots is supported.

For example if you want to send a toot every hour on a schedule you can.

```yaml
skills:
  speakingclock:
    path: speakingclock.py
```

```python
# speakingclock.py
from opsdroid.skill import Skill
from opsdroid.matchers import match_crontab
from opsdroid.events import Message

from datetime import datetime

class SpeakingClockSkill(Skill):
    @match_crontab('0 * * * *')
    async def speakingclock(self, event):
        await self.opsdroid.send(Message(text=f"The time is now {datetime.now().strftime('%T')}"))
```

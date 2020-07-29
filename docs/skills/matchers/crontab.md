# Crontab

The crontab matcher takes a [cron timing](https://en.wikipedia.org/wiki/Cron). It allows you to schedule skills to be called on an interval instead of being triggered by events.

```eval_rst
.. autofunction:: opsdroid.matchers.match_crontab
```

## Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_crontab
from opsdroid.events import Message

class CrontabSkill(Skill):
    @match_crontab('* * * * *', timezone="Europe/London")
    async def mycrontabskill(self, event):
        await self.opsdroid.send(Message(text="Hey"))
```

The above skill would be called every minute. The skill then asks opsdroid to send a message with the text `Hey` and because we do not tell opsdroid where to send the message it will be sent to the default target of the default connector. You can also access these defaults yourself at `opsdroid.default_connector` and `opsdroid.default_connector.default_target`.

You can also set the timezone that the skill crontab is aligned with. This is useful if you want to have different time zones between skills. This kwarg is optional, if not set it will default to the timezone specified in the root of the configuration or failing that UTC.

You may also want to be able to configure where messages are sent by default on a skill by skill basis.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_crontab
from opsdroid.events import Message

class CrontabSkill(Skill):
    @match_crontab('* * * * *', timezone="Europe/London")
    async def mycrontabskill(self, event):
        await self.opsdroid.send(
            Message(
                text="Hey",
                connector=self.config.get("default-connector"),
                target=self.config.get("default-target")
            )
        )
```

```yaml
# ...

skills:
  mycrontabskills:
    path: /path/to/skill
    default-connector: "slack"
    default-target: "#random"
```

In the above example we are specifying that the message should be sent to Slack in the `#random` room by setting these values in our config and accessing them within the skill. If we removed the configuration options then the `self.config.get` calls would return `None` and opsdroid would again fall back to the main defaults from the first example.

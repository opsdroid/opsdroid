# Crontab Matcher

## Configuring opsdroid

In order to enable crontab skills you must set the `enabled` parameter to true in the parsers section of the opsdroid configuration file.

```yaml
parsers:
  crontab:
    enabled: true
```

##

The crontab matcher is a bit different to other matchers. This matcher doesn't take a message as an input, it takes a [cron timing](https://en.wikipedia.org/wiki/Cron) instead. It allows you to schedule skills to be called on an interval instead of being triggered by messages.

## Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_crontab
from opsdroid.events import Message

class CrontabSkill(Skill):
    @match_crontab('* * * * *', timezone="Europe/London")
    async def mycrontabskill(self, message):

        # Get the default connector
        connector = self.opsdroid.default_connector

        # Get the default room for that connector
        room = connector.default_target

        # Create an empty message to respond to
        message = Message("", None, room, connector)

        # Respond
        await message.respond('Hey')
```

The above skill would be called every minute. As the skill is being triggered by something other than a message the `message` argument being passed in will be set to `None`, this means you need to create an empty message to respond to. You will also need to know which connector, and possibly which room, to send the message back to. For this you can use the `opsdroid.default_connector` and `opsdroid.default_connector.default_target` properties to get some sensible defaults.

You can also set the timezone that the skill crontab is aligned with. This is useful if you want to have different time zones between skills. This kwarg is optional, if not set it will default to the timezone specified in the root of the configuration or failing that UTC.

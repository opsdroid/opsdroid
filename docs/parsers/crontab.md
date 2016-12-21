# Crontab Parser

The crontab parser is a bit different to other parsers. This parser doesn't take a message as an input, it takes a [cron timing](https://en.wikipedia.org/wiki/Cron) instead. It allows you to schedule skills to be called on an interval instead of being triggered by messages.

## Example

```python
from opsdroid.skills import match_crontab

@match_crontab('* * * * *')
async def mycrontabskill(opsdroid):

    # Get the default connector
    connector = opsdroid.default_connector

    # Get the default room for that connector
    room = connector.default_room

    # Create an empty message to respond to
    message = Message("", None, room, connector)

    # Respond
    await message.respond('Hey')
```

The above skill would be called every minute. As the skill is being triggered by something other than a message you need to create an empty message to respond to. You will also need to know which connector, and possibly which room, to send the message back to. For this you can use the `opsdroid.default_connector` and `opsdroid.default_connector.default_room` properties to get some sensible defaults.

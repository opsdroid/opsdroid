# Webhook Parser

Similar to the crontab matcher this matcher doesn't take a message as an input, it takes a webhook instead. It allows you to trigger the skill by calling a specific URL endpoint.

## Example

```python
from aiohttp.web import Request

from opsdroid.matchers import match_webhook
from opsdroid.message import Message

@match_webhook('examplewebhook')
async def mycrontabskill(opsdroid, config, message):

    if type(message) is not Message and type(message) is Request:
      # Capture the request POST data and set message to a default message
      request = await message.post()
      message = Message("", None, connector.default_room,
                        opsdroid.default_connector)

    # Respond
    await message.respond('Hey')
```

**Config**

```yaml
skills:
  - name: "exampleskill"
```

The above skill would be called if you send a POST to `http://localhost:8080/skill/exampleskill/examplewebhook`. As the skill is being triggered by a webhook the `message` argument being passed in will be set to the [aiohttp Request](http://aiohttp.readthedocs.io/en/stable/web_reference.html#aiohttp.web.BaseRequest), this means you need to create an empty message to respond to. You will also need to know which connector, and possibly which room, to send the message back to. For this you can use the `opsdroid.default_connector` and `opsdroid.default_connector.default_room` properties to get some sensible defaults.

# Webhook Matcher

**Config**

```yaml
skills:
  - name: "exampleskill"
```

The above skill would be called if you send a POST to `http://localhost:8080/skill/exampleskill/examplewebhook`. As the skill is being triggered by a webhook the `message` argument being passed in will be set to the [aiohttp Request](http://aiohttp.readthedocs.io/en/stable/web_reference.html#aiohttp.web.BaseRequest), this means you need to create an empty message to respond to. You will also need to know which connector, and possibly which room, to send the message back to. For this you can use the `opsdroid.default_connector` and `opsdroid.default_connector.default_room` properties to get some sensible defaults.

Similar to the crontab matcher this matcher doesn't take a message as an input, it takes a webhook instead. It allows you to trigger the skill by calling a specific URL endpoint.

## Example

```python
from aiohttp.web import Request

from opsdroid.skill import Skill
from opsdroid.matchers import match_webhook
from opsdroid.events import Message

class MySkill(Skill):
    @match_webhook('examplewebhook')
    async def mywebhookskill(self, message):

        if type(message) is not Message and type(message) is Request:
          # Capture the request POST data and set message to a default message
          request = await message.post()
          message = Message("", None, self.opsdroid.connector.default_room,
                            self.opsdroid.default_connector)

        # Respond
        await message.respond('Hey')
```

## Custom Responses

You can also return a custom `Response` object from your skill if you need to given a certain body or status code back to the service that called the webhook. If you do not do this then opsdroid will respond with a 200 by default and a json body of `{"called_skill": "<webhook name>"}`.

```python
from aiohttp.web import Request, Response

from opsdroid.skill import Skill
from opsdroid.matchers import match_webhook
from opsdroid.message import Message

class MySkill(Skill):
    @match_webhook('examplewebhook')
    async def mywebhookskill(self, message):

        if type(message) is not Message and type(message) is Request:
          # Capture the request POST data and set message to a default message
          request = await message.post()
          message = Message("", None, self.opsdroid.connector.default_room,
                            self.opsdroid.default_connector)

        # Respond
        await message.respond('Hey')
        return Response(body='my custom response', status=201)
```
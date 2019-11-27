# Webhooks

The webhook matcher allows you to trigger the skill by calling a specific URL endpoint.

```eval_rst
.. autofunction:: opsdroid.matchers.match_webhook
```

## Example

```python
# /path/to/my/exampleskill/__init__.py

from aiohttp.web import Request

from opsdroid.skill import Skill
from opsdroid.matchers import match_webhook
from opsdroid.events import Message

class MySkill(Skill):
    @match_webhook('examplewebhook')
    async def mywebhookskill(self, event: Request):
        # Capture the post data
        data = await event.json()

        # Respond with the data in the default room on the default connector
        await self.opsdroid.send(Message(str(data)))
```

The above skill would be called if you send a POST to `http://localhost:8080/skill/exampleskill/examplewebhook`. The skill is being triggered by a webhook and so the `event` argument being passed in will be set to the [aiohttp Request](http://aiohttp.readthedocs.io/en/stable/web_reference.html#aiohttp.web.BaseRequest) object. You may also want to trigger actions to happen in a chat connector, for this you can use `opsdroid.send` to send a message to the default target in the default connector. You could also explore the `opsdroid.connectors` list and call `connector.send` on a specific connector.

## Custom Responses

You can also return a custom `Response` object from your skill if you need to given a certain body or status code back to the service that called the webhook. If you do not do this then opsdroid will respond with a 200 by default and a json body of `{"called_skill": "<webhook name>"}`.

```python
from aiohttp.web import Request, Response

from opsdroid.skill import Skill
from opsdroid.matchers import match_webhook
from opsdroid.events import Message

class MySkill(Skill):
    @match_webhook('examplewebhook')
    async def mywebhookskill(self, event: Request):
        # Capture the post data
        data = await event.json()

        # Respond with the data in the default room on the default connector
        await self.opsdroid.send(Message(str(data)))

        # Send a custom aiohttp.web.Response object back to the webhook
        return Response(body='my custom response', status=201)
```
## Securing Webhooks

You can also secure the webhooks by adding an optional `webhook-token` value to the `web` configuration. This enables a token-based authentication where the `POST` request is required to have an `Authorization` header with the bearer token as its value.

**Example Config**

```yaml
web:
  webhook-token: "aabbccddee"
```

**Example POST Request using Curl**

```
curl -X POST -H "Authorization: Bearer aabbccddee" http://localhost:8080/skill/exampleskill/examplewebhook
```

# api.ai Parser

[api.ai](https://api.ai) is an NLP API for matching strings to [intents](https://docs.api.ai/docs/concept-intents) or [actions](https://docs.api.ai/docs/concept-actions). Intents are created on the api.ai website.

## Example 1

```python
from opsdroid.skills import match_apiai_action

@match_apiai_action('mydomain.myaction')
async def mySkill(opsdroid, message):
    await message.respond('An appropriate response!')
```

The above skill would be called on any intent which has an action of `'mydomain.myaction'`.

## Example 2

```python
from opsdroid.skills import match_apiai_intent

@match_apiai_intent('myIntent')
async def mySkill(opsdroid, message):
    await message.respond('An appropriate response!')
```

The above skill would be called on any intent which has a name of `'myIntent'`.

## Creating an api.ai bot

You can find a quick getting started with api.ai guide [here](https://docs.api.ai/docs/get-started).

## Configuring opsdroid

In order to enable api.ai skills you must specify an `access-key` for your bot (referred to as an agent in api.ai) in the parsers section of the opsdroid configuration file. You can find this `access-key` in your agent settings. Currently you may only register one agent per opsdroid instance to avoid making multiple API calls for every message.

You can also set a `min-score` option to tell opsdroid to ignore any matches which score less than a given number between 0 and 1. The default for this is 0 which will match all messages.

```yaml

parsers:
  apiai:
    access-token: "exampleaccesstoken123"
    min-score: 0.6
```

## Message object additional parameters

### `message.apiai`

An http response object which has been returned by the api.ai API. This allows you to access any information from the matched intent including the action, intent name, suggested speech response, context, parameters, score, error status, etc.

```python
import json

from opsdroid.skills import match_apiai_action

@match_apiai_action('smalltalk.greetings')
async def dumpResponse(opsdroid, message):
    print(json.dumps(message.apiai))
```

This example skill will print the following on the message "whats up?".

```json
{
  "sessionId": "abc123",
  "result": {
    "parameters": {
      "simplified": "what is up"
    },
    "metadata": {
      "contexts": [],
      "outputContexts": [],
      "inputContexts": []
    },
    "speech": "Living the dream.",
    "action": "smalltalk.greetings",
    "resolvedQuery": "whats up?",
    "source": "domains",
    "score": 1.0
  },
  "timestamp": "2016-12-19T12:10:20.462Z",
  "id": "9835915f-72a8-4292-8365-3067b9af0a80",
  "status": {
    "errorType": "success",
    "code": 200
  }
}
```

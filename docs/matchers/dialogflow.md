# Dialogflow Matcher (previously Api.ai)

[Dialogflow](https://dialogflow.com/) is an NLP API for matching strings to [intents](https://dialogflow.com/docs/intents) or [actions](https://dialogflow.com/docs/concept-actions). Intents are created on the Dialogflow website.

## Example 1

```python
from opsdroid.matchers import match_dialogflow_action

@match_dialogflow_action('mydomain.myaction')
async def my_skill(opsdroid, config, message):
    await message.respond('An appropriate response!')
```

The above skill would be called on any intent which has an action of `'mydomain.myaction'`.

## Example 2

```python
from opsdroid.matchers import match_dialogflow_intent

@match_dialogflow_intent('myIntent')
async def my_skill(opsdroid, config, message):
    await message.respond('An appropriate response!')
```

The above skill would be called on any intent which has a name of `'myIntent'`.

## Creating a Dialogflow bot

You can find a quick getting started with Dialogflow guide [here](https://dialogflow.com/docs/getting-started/basics).

If you want to use Dialogflow in a different language other than English, all you need to do is specify the `lang` parameter in Opsdroid's configuration. Then change/add another language to your Dialogflow agent in the Language tab of the agent settings.

_Useful Links: [Languages Reference](https://dialogflow.com/docs/reference/language), [Multi-language Agents Reference](https://dialogflow.com/docs/multi-language)_


## Configuring opsdroid

In order to enable Dialogflow skills you must specify an `access-key` for your bot (referred to as an agent in Dialogflow) in the matchers section of the opsdroid configuration file. You can find this `access-key` in your agent settings. Currently you may only register one agent per opsdroid instance to avoid making multiple API calls for every message.

You can also set a `min-score` option to tell opsdroid to ignore any matches which score less than a given number between 0 and 1. The default for this is 0 which will match all messages.

```yaml

parsers:
  - name: dialogflow
    access-token: "exampleaccesstoken123"
    min-score: 0.6
```

## Message object additional parameters

### `message.dialogflow`

An http response object which has been returned by the Dialogflow API. This allows you to access any information from the matched intent including the action, intent name, suggested speech response, context, parameters, score, error status, etc.

```python
import json

from opsdroid.matchers import match_dialogflow_action

@match_dialogflow_action('smalltalk.greetings')
async def dump_response(opsdroid, config, message):
    print(json.dumps(message.dialogflow))
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

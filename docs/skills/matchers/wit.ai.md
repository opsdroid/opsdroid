# Wit.ai

## Configuring opsdroid

In order to enable wit.ai skills, you must specify an `token` for your bot in the parsers section of the opsdroid configuration file.
You can find this `token` in the settings of your App under the name: `'Server Access Token: '`.

You can also set a `min-score` option to tell opsdroid to ignore any matches which score less than a given number between 0 and 1. The default for this is 0 which will match all messages.

```yaml

parsers:
  witai:
    token: XJF475SKGITJ98KHFO
    min-score: 0.6
```

[wit.ai](https://wit.ai) is an NLP API for matching strings to [intents](https://wit.ai/docs/recipes#categorize-the-user-intent). Intents are created on the wit.ai website.

```eval_rst
.. autofunction:: opsdroid.matchers.match_witai
```

## [Example 1](#example1)

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_witai

class MySkill(Skill):
    @match_witai('get_weather')
    async def weather(self, message):
        """Hard Coded version of weather function"""
        temp = 10
        humidity = "80%"
        city = message.witai['entities']['location'][0]['value']
        status = "Clouds"

        await message.respond("It's currently {} degrees, {}% humidity in {} and {} is forecasted "
                              "for today".format(temp, humidity, city, status))
```

The above skill would be called on any intent which has a name of `'get_weather'`.

#### Usage example

> user: what's the weather like in London
>
> opsdroid: It's currently 13.12 degrees, 67% humidity in London and Rain is forecasted for today

## Creating a wit.ai App
You need to register on wit.ai and create an App in order to use wit.ai with opsdroid.

You can find a quick getting started with the wit.ai guide [here](https://wit.ai/getting-started).

If you want to use wit.ai in a different language other than English, all you need to do is change the language of your app located in the app settings.

## Message object additional parameters

### `message.witai`

An http response object which has been returned by the wit.ai API. This allows you to access any information from the matched intent including other entities, intents, values, etc.


## Example Skill

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_witai

import json

class MySkill(Skill):
    @match_witai('get_weather')
    async def dumpResponse(self, message):
        print(json.dumps(message.witai))
```

### Return Value on "How's the weather?"

The example skill will print the following on the message "how's the weather?".

```json
{
  "msg_id": "0zTl3L16kFW4PwtSt",
  "_text": "how's the weather",
  "entities": {
     "intent": [
       {
         "confidence": 0.77586417870417,
         "value": "get_weather"
       }
     ]
  }
}
```

## Return Value on "What's the weather like in London?"

The example skill will print the following on the message "What's the weather like in London?".

```json
{
   "msg_id": "0zrCQ5LEkWd0MoHYM",
   "_text": "What's the weather like in London?",
   "entities": {
      "location": [
        {
          "suggested": true,
          "confidence": 0.74044071131585,
          "value": "London",
          "type": "value"
        }
      ],
      "intent": [
        {
          "confidence": 0.99979499373014,
          "value": "get_weather"
        }
      ]
   }
}

```

Since Wit.ai can recognise locations, you can use this values on your skills to return different things.
On our weather skill([example 1](#example1)) we changed the city param to get the temperature related to any city passed on the message.

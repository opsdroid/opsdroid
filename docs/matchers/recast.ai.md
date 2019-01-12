# Recast.AI Matcher

## Configuring opsdroid

In order to enable Recast.AI skills, you must specify an `access-token` for your bot in the parsers section of the opsdroid configuration file.
You can find this `access-token` in the settings of your bot under the name: `'Request access token'`.

You can also set a `min-score` option to tell opsdroid to ignore any matches which score less than a given number between 0 and 1. The default for this is 0 which will match all messages.

```yaml

parsers:
  - name: recastai
    access-token: 85769fjoso084jd
    min-score: 0.8
```

##

[Recast.AI](https://recast.ai/) is an NLP API for matching strings to [intents](https://recast.ai/docs/intent). Intents are created on the Recast.AI website.

## [Example 1](#example1)

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_recastai

class MySkill(Skill):
    @match_recastai('greetings')
    async def hello(self, message):
        """Replies to user when any 'greetings'
        intent is returned by Recast.AI
        """
        await message.respond("Hello there!")
```

The above skill would be called on any intent which has a name of `'greetings'`.

## Example 2

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_recastai

class MySkill(Skill):
    @match_recastai('ask-joke')
    async def my_skill(self, message):
        """Returns a joke if asked by the user"""
        await message.respond('What do you call a bear with no teeth? -- A gummy bear!')
```

The above skill would be called on any intent which has a name of `'ask-joke'`.


## Creating a Recast.AI bot
You need to [register](https://recast.ai/signup) on Recast.AI and create a bot in order to use Recast.AI with opsdroid.

You can find a quick getting started with the Recast.AI guide [here](https://recast.ai/docs/create-your-bot).

If you want to use Recast.AI in a different language other than English, all you need to do is specify the `lang` parameter in opsdroid's configuration.

_Note: "If you do not have any expressions in this language, we will use your default bot language for processing." - [Recast.AI Language page](https://recast.ai/docs/language)_

## Message object additional parameters

### `message.recastai`

An http response object which has been returned by the Recast.AI API. This allows you to access any information from the matched intent including other entities, intents, values, etc.


## Example Skill

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_recastai

import json

class MySkill(Skill):
    @match_recastai('ask-feeling')
    async def dumpResponse(self, message):
        print(json.dumps(message.recastai))
```

### Return Value on "How are you?"

The example skill will print the following on the message "how are you?".

```json
{
    "results":
      {
        "uuid": "cab86e23-caaf-4131-9b83-a564887203da",
        "source": "how are you?",
        "intents": [
          {
            "slug": "ask-feeling",
            "confidence": 0.99
           }
        ],
        "act": "wh-query",
        "type": "desc:manner",
        "sentiment": "neutral",
        "entities":
          {
            "pronoun": [
              {
                "person": 2,
                "number": "singular",
                "gender": "unknown",
                "raw": "you",
                "confidence": 0.99
              }
            ]
          },
        "language": "en",
        "processing_language": "en",
        "version": "2.10.1",
        "timestamp": "2017-11-15T11:50:51.478057+00:00",
        "status": 200},
        "message": "Requests rendered with success"
      }
}
```



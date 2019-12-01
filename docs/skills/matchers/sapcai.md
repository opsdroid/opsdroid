# SAP Conversational AI (previously Recast.ai)

## Configuring opsdroid

[SAP Conversational AI](https://cai.tools.sap/) is an NLP API for matching strings to [intents](https://cai.tools.sap/docs/concepts/intent). Intents are created on the SAP Conversational AI website.

In order to enable SAP Conversational AI skills, you must specify an `token` for your bot in the parsers section of the opsdroid configuration file.
You can find this `token` in the settings of your bot. Click on the Tokens tab and use the `'Developer token'` details.

You can also set a `min-score` option to tell opsdroid to ignore any matches which score less than a given number between 0 and 1. The default for this is 0 which will match all messages.

```yaml

parsers:
  sapcai:
    token: 85769fjoso084jd
    min-score: 0.8
```

### Localization

If you use opsdroid in a language other than English, this parser will automatically grab the language code that you have set on your configuration.

If you want to run this parser in a different language you can overwrite the language configuration by adding the `lang` parameter on this parser configuration.

_Note: You need to make sure that your intent has the language that you wish to parse added to it. Click the intent name and choose 'Add Language'._

#### Example

```yaml
parsers:
  sapcai:
    token: 85769fjoso084jd
    min-score: 0.8
    lang: 'pt'
```

This will make the parser to use the Portuguese language when matching the string to an intent.

## Using the parser with a skill

Let's have a look at how you can use this parser and the `match_sapcai` decorator on a skill.

The `match_sapcai` decorator takes one parameter (the name of the intent to match), any skill (function or class method) decorated with this matcher, will trigger that skill.

```eval_rst
.. autofunction:: opsdroid.matchers.match_sapcai
```

### [Example 1](#example1)

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_sapcai

class MySkill(Skill):
    @match_sapcai('greetings')
    async def hello(self, message):
        """Replies to user when any 'greetings'
        intent is returned by SAP Conversational AI
        """
        await message.respond("Hello there!")
```

The above skill would be called on any intent which has a name of `'greetings'`.

### Example 2

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_sapcai

class MySkill(Skill):
    @match_sapcai('ask-joke')
    async def my_skill(self, message):
        """Returns a joke if asked by the user"""
        await message.respond('What do you call a bear with no teeth? -- A gummy bear!')
```

The above skill would be called on any intent which has a name of `'ask-joke'`.

## Creating a SAP Conversational AI bot

You need to [register](https://cai.tools.sap/signup) on SAP Conversational AI and create a bot in order to use SAP Conversational AI with opsdroid.

You can find a quick getting started with the SAP Conversational AI guide [here](https://cai.tools.sap/docs/concepts/create-builder-bot).

## Message object additional parameters

### `message.recastai`

An http response object which has been returned by the SAP Conversational AI API. This allows you to access any information from the matched intent including other entities, intents, values, etc.

## Example Skill

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_sapcai

import json

class MySkill(Skill):
    @match_sapcai('ask-feeling')
    async def dump_response(self, message):
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
        "status": 200,
        "message": "Requests rendered with success"
      }
}
```

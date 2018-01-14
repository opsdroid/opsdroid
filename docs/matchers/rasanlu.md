# Rasa NLU Matcher

[Rasa NLU](https://github.com/RasaHQ/rasa_nlu) is an open source tool for running your own NLP API for matching strings to [intents](https://rasahq.github.io/rasa_nlu/). This is the recommended parser if you have privacy concerns but want the power of a full NLU parsing engine.

Rasa NLU is also trained via the API and so opsdroid can do the training for you if you provide an intents [markdown file](https://rasahq.github.io/rasa_nlu/dataformat.html#markdown-format) along with your skill. This file must contain headers in the format `## intent:<intent name>` followed by a list of example phrases for that intent. Rasa NLU will then use those examples to build a statistical model for matching new and unseen variations on those sentences.

> ⚠️ **Warning** - Rasa NLU requires 4GB of memory, 2GB for training models and 2GB for serving requests. If you do not provide enough it will hang and cause timeouts in opsdroid.

## [Example 1](#example1)

Skill file (`__init__.py`).
```python
from opsdroid.matchers import match_rasanlu

@match_rasanlu('greetings')
async def hello(opsdroid, config, message):
    """Replies to user when any 'greetings' 
    intent is returned by Rasa NLU
    """
    await message.respond("Hello there!")
```

Intents file (`intents.md`).
```markdown
## intent:greetings
- Hey
- Hello
- Hi
- Hiya
- hey
- whats up
- wazzup
- heya
```

The above skill would be called on any intent which has a name of `'greetings'`. 

## Example 2

Skill file (`__init__.py`).
```python
from opsdroid.matchers import match_rasanlu

@match_rasanlu('ask-joke')
async def my_skill(opsdroid, config, message):
    """Returns a joke if asked by the user"""
    await message.respond('What do you call a bear with no teeth? -- A gummy bear!')
```

Intents file (`intents.md`).
```markdown
## intent:ask-joke
- Tell me a joke
- Say something funny
- Do you know any jokes?
- Tell me something funny
- Can you tell jokes?
- Do you know jokes?
```

The above skill would be called on any intent which has a name of `'ask-joke'`.

## Configuring opsdroid

In order to enable Rasa NLU skills, you can tell opsdroid where to find your Rasa NLU instance in the parsers section of the opsdroid configuration file. You can set the `url` and `project` parameters which default to `http://localhost:5000` and `opsdroid` respectively.

Projects in Rasa NLU are separate areas for training and storing your intent models. This is useful as you can have multiple instances of opesdroid (or even other applications) sharing one instance of Rasa NLU if you configure them with different project names.

Rasa NLU gives you the option to set a password or `token` which must be provided when interacting with the API. You can optionally set this in the parser config too.

You can also set a `min-score` option to tell opsdroid to ignore any matches which score less than a given number between 0 and 1. The default for this is 0 which will match all messages.

```yaml

parsers:
  - name: rasanlu
    url: http://localhost:5000
    project: opsdroid
    token: 85769fjoso084jd
    min-score: 0.8
```

## Message object additional parameters

### `message.rasanlu`

An http response object which has been returned by the Rasa NLU API. This allows you to access any information from the matched intent including other entities, intents, values, etc.


## Example Skill

```python
from opsdroid.matchers import match_rasanlu

import json


@match_rasanlu('restaurants')
async def dumpResponse(opsdroid, config, message):
    print(json.dumps(message.rasanlu))
```

### Return Value on "I am looking for a Mexican restaurant in the center of town"

The example skill will print the following .

```json
{
  "intent": "search_restaurant",
  "entities": {
    "cuisine" : "Mexican",
    "location" : "center"
  }
}
```



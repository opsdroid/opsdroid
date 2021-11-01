# Rasa NLU

## Configuring opsdroid

In order to enable Rasa NLU skills, you can tell opsdroid where to find your Rasa NLU instance in the parsers section of the opsdroid configuration file. You can set the `url` parameter, which defaults to `http://localhost:5000`.

Rasa NLU gives you the option to set a password or `token` which must be provided when interacting with the API. You can optionally set this in the parser config too.

You can also set a `min-score` option to tell opsdroid to ignore any matches which score less than a given number between 0 and 1. The default for this is 0 which will match all messages.

`models-path` is used to load the model in Rasa. It defaults to `models`. If your Rasa instance writes trained models somewhere else, you can set this option to whatever path you need.

`train` is used to make opsdroid train your model on each start. Setting this configuration flag to `False` allows you to use a previously trained
model.

```yaml

parsers:
  rasanlu:
    url: http://localhost:5000
    models-path: models
    token: 85769fjoso084jd
    min-score: 0.8
    train: True
```

[Rasa NLU](https://github.com/RasaHQ/rasa) is an open source tool for running your own NLP API for matching strings to [intents](https://rasa.com/docs/rasa/). This is the recommended parser if you have privacy concerns but want the power of a full NLU parsing engine.

Rasa NLU is also trained via the [API](https://rasa.com/docs/rasa/pages/http-api) and so opsdroid can do the training for you if you provide an intents [YAML file](https://rasa.com/docs/rasa/nlu-training-data) along with your skill. This file must contain intents with headers in the format `- intent: <intent name>` followed by a list of example phrases for that intent. Rasa NLU will then use those examples to build a statistical model for matching new and unseen variations on those sentences.


> **Note** - Rasa version >= 2.x.x is supported.

```eval_rst
.. warning::
   Rasa NLU requires 4GB of memory, 2GB for training models and 2GB for serving requests. If you do not provide enough it will hang and cause timeouts in opsdroid.
```

```eval_rst
.. autofunction:: opsdroid.matchers.match_rasanlu
```

For developing or testing purposes you can run Rasa manually inside a container using:

```
docker run \
    --rm -ti \
    -p 5005:5005 \
    --name rasa \
    rasa/rasa:2.6.2-full \
    run --enable-api --auth-token 85769fjoso084jd -vv
```

## [Example 1](#example1)

Skill file (`__init__.py`).
```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_rasanlu

class MySkill(Skill):
    @match_rasanlu('greetings')
    async def hello(self, message):
        """Replies to user when any 'greetings'
        intent is returned by Rasa NLU
        """
        await message.respond("Hello there!")

    @match_rasanlu('bye')
    async def bye(self, message):
        """Replies to user when any 'greetings'
        intent is returned by Rasa NLU
        """
        await message.respond("See ya!")
```

Intents file (`intents.yml`).
```yaml
version: "2.0"

nlu:
- intent: greetings
  examples: |
    - Hey
    - Hello
    - Hi
    - Hiya
    - hey
    - whats up
    - wazzup
    - heya
- intent: bye
  examples: |
    - googbye
    - bye
    - ciao
    - see you
```

> **Note** - Rasa NLU requires an intent to have at least three training examples in the list. There must also be a minimum of two intents in your file for Rasa to train.

The above skill would be called on any intent which has a name of `'greetings'` and `'bye'`.

## Example 2

Skill file (`__init__.py`).
```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_rasanlu

class MySkill(Skill):
    @match_rasanlu('ask-joke')
    async def my_skill(self, message):
        """Returns a joke if asked by the user"""
        await message.respond('What do you call a bear with no teeth? -- A gummy bear!')
```

Intents file (`intents.yml`).
```yaml
version: "2.0"

nlu:
- intent: greetings
  examples: |
    - Hey
    - Hello
    - Hi
- intent: ask-joke
  examples: |
    - Tell me a joke
    - Say something funny
    - Do you know any jokes?
    - Tell me something funny
    - Can you tell jokes?
    - Do you know jokes?
```

The above skill would be called on any intent which has a name of `'ask-joke'`.

## Message object additional parameters

### `message.rasanlu`

An http response object which has been returned by the Rasa NLU API. This allows you to access any information from the matched intent including other entities, intents, values, etc.


## Example Skill

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_rasanlu

import json

class MySkill(Skill):
    @match_rasanlu('restaurants')
    async def dumpResponse(self, message):
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

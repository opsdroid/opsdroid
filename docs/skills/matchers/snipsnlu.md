# Snips NLU

## Configuring opsdroid

In order to enable Snips NLU skills, you can tell opsdroid where to find your Snips NLU instance in the parsers section of the opsdroid configuration file. You can set the directory and parameters.

Projects in Sinps NLU are separate areas for training and storing your intent models. This is useful as you can have multiple instances of opsdroid (or even other applications) sharing one instance of Snips NLU if you configure them with different project names.

```yaml

parsers:
  snipsnlu:
    dir:
```

[Snips NLU](https://github.com/snipsco/snips-nlu) is an open source tool for running your own NLP API for matching strings to [intents](https://snips-nlu.readthedocs.io/en/latest/). This is the recommended parser if you have privacy concerns but want the power of a full NLU parsing engine.

Snips NLU is also trained via the API and so opsdroid can do the training for you if you provide an intents [markdown file](https://snips-nlu.readthedocs.io/en/latest/dataset.html) along with your skill. This file must contain headers in the format `## intent:<intent name>` followed by a list of example phrases for that intent. Snips NLU will then use those examples to build a statistical model for matching new and unseen variations on those sentences.

```eval_rst
.. autofunction:: opsdroid.matchers.match_snipsnlu
```

## [Example 1](#example1)

Skill file (`__init__.py`).
```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_snipsnlu

class MySkill(Skill):
    @match_snipsnlu('searchFlight'):
        async def hello(self, message):
        """Replies to user search for any flight
        intent is returned by Snips NLU
        """
        await message.respond("find me a flight from Paris to New York")
```

Intents file (`intents.yml`).
```yaml
type: intent
name: searchFlight
slots:
  - name: origin
    entity: city
  - name: destination
    entity: city
  - name: date
    entity: snips/datetime
utterances:
  - find me a flight from [origin](Paris) to [destination](New York)
  - I need a flight leaving [date](this weekend) to [destination](Berlin)
  - show me flights to go to [destination](new york) leaving [date](this evening)

# City Entity
---
type: entity
name: city
values:
  - london
  - [new york, big apple]
  - [paris, city of lights]
```

> **Note** - Snips NLU requires an intent to have at least three training examples in the list. There must also be a minimum of two intents in your file for Rasa to train.

The above skill would be called on any intent which has a name of `'searchFlight'`.

## Example 2

Skill file (`__init__.py`).
```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_snipsnlu

class MySkill(Skill):
    @match_snipsnlu('turnLightOn')
    async def my_skill(self, message):
        """Returns a joke if asked by the user"""
        await message.respond('switch the bedroom\'s lights on please')
```

Intents file (`intents.yml`).
```yaml
# turnLightOn intent
---
type: intent
name: turnLightOn
slots:
  - name: room
    entity: room
utterances:
  - Turn on the lights in the [room](kitchen)
  - give me some light in the [room](bathroom) please
  - Can you light up the [room](living room) ?
  - switch the [room](bedroom)'s lights on please

```

The above skill would be called on any intent which has a name of `'turnLightOn'`.

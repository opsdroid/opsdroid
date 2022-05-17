# Flip A Coin

A skill for opsdroid to perform flipping a coin.

## Setting Up

First we must create an opsdroid skill directory. This can be anywhere on your filesystem, we just need to remember
where for later. For this example we will make a new folder in `~/opsdroid/skills`.

```shell
$ mkdir -p ~/opsdroid/skills/flip-coin
```

## The skill

Then inside this folder we need to create a file called  `__init__.py` and import the following packages:

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

import random
```

Second, create a class for the skill:

```python
class CoinSkill(Skill):
    @match_regex('flip a coin')
    async def flip_a_coin(self, message):
        if random.randint(0, 1):
            response = "Heads"
        else:
            response = "Tails"

        await message.respond("{}".format(response))

```

## Configuration

Third, open you 'configuration.yaml' file. You can do this automatically with the `opsdroid config edit` command.

Then add the following to the skills section.

```yaml
skills:
  flip-a-coin:
  path: ~/opsdroid/skills/flip-coin
```

Now save your configuration and reload opsdroid.

For more examples of skills you can build with opsdroid checkout our [examples section](../examples/index.md).

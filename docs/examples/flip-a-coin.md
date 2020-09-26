# Flip A Coin

A skill for opsdroid to perform flipping a coin.

## Setting Up

Navigating to 'opsdroid/skills/' there is a file called '__init__.py' in which will contain the functions for opsdroid to flip a coin.

## Configure

First, in the `__init__.py` file include the following packages:

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
        flip = random.randint(0, 1)
        if flip:
            res = "Heads"
        else:
            res = "Tails"
        
        await message.respond("{}".format(res))

```

Third, open the 'configuration.yaml' file and add the path:

```yaml
skills:
    flip-a-coin:
    path: ~/skill-flipacoin
```
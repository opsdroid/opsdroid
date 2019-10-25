# opsdroid skill-random

A skill for [opsdroid](https://github.com/opsdroid/opsdroid) to perform random events like flipping a coin or rolling a dice.
## Creating skills

Skills are designed to be simpler than other modules to ensure that it is easy to get started.

To create a skill you need to at minimum create a single python file in your repository with the  `__init__.py`  name. For example the skill  `hello`  has a single file called  `__init__.py`.

##  Configuration
```yaml
None.
```

## Writing the skill
```python

from opsdroid.matchers import match_regex
import random


DICE_ROLL_RESPONSES = [

	"The dice says {number}",

	"You rolled a {number}",

	"It's a {number}"

]

COIN_FLIP_RESPONSES = [
	
	"It landed on {result}",

	"You got {result}",

	"It's {result}"

]

@match_regex(r'roll a dice', case_sensitive=False)

async def roll_a_dice(opsdroid, config, message):

	number = random.randint(1,6)

	text = random.choice(DICE_ROLL_RESPONSES).format(number=number)

	await message.respond(text)

@match_regex(r'flip a coin', case_sensitive=False)

async def flip_a_coin(opsdroid, config, message):

	result = random.choice(["heads", "tails"])

	text = random.choice(COIN_FLIP_RESPONSES).format(result=result)

	await message.respond(text)
```
## Demonstrating

    Flip a coin
   Flips a coin.

> user: flip a coin
>opsdroid: It landed on heads

    roll a dice
   Rolls a dice.
   

> user: roll a dice
>opsdroid: You rolled a 4

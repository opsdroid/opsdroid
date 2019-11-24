# Parse Format

## About Parse Format Matcher

This is the simplest matcher available in opsdroid. It matches the message from the user against a string with Python [format syntax](https://docs.python.org/3/library/string.html#format-string-syntax). If the string matches then the function is called.

The third party library [parse](https://github.com/r1chardj0n3s/parse) is used to parse the strings.

You can specify which kind of matching you want to apply through the `matching_condition` kwarg (*match* matching is the default).

```eval_rst
.. warning::
   Be careful, the matching condition names are the same than in regex but there are some differences between them.
```

Matching conditions:

- **match** - Scans through the string looking at the beginning of the string to match the pattern, **but the end must match too**. So if you have `hi` it will match `hi`, but not `say hi` or `hi!`.
- **search** - Scans through the string looking for the first location where the pattern produces a match, and ignores what is before or after the match. So if you have `hi` it will match `hi`, `say hi` or `hi!`.

```eval_rst
.. autofunction:: opsdroid.matchers.match_parse
```


### (Very) Basic example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_parse
import random

class MySkill(Skill):
    @match_parse('hi')
    async def hello(self, message):
        text = random.choice(['Hi {}', 'Hello {}', 'Hey {}']).format(message.user)
        await message.respond(text)
```

When we run opsdroid and send the message `hi` opsdroid will match to the skill and reply immediately. Opsdroid will only trigger the skill if *hi* is the only word in the message.

```
[6:13:11 PM] HichamTerkiba:
hi

[6:13:12 PM] opsdroid:
Hi HichamTerkiba

[6:13:16 PM] HichamTerkiba:
I said hi

<No reply from opsdroid>
```

### Example 2 - match condition

Let's use the following hello skill with the kwarg `matching_condition='search'`.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_parse
import random

class MySkill(Skill):
    @match_parse('hi', case_sensitive=False, matching_condition='search')
    async def hello(self, message):
        text = random.choice(['Hi {}', 'Hello {}', 'Hey {}']).format(message.user)
        await message.respond(text)
```

With the matching condition kwarg set to search and case sensitive set to `False`, opsdroid will be more flexible.

```
[6:13:11 PM] HichamTerkiba:
Hi opsdroid!

[6:13:12 PM] opsdroid:
Hi HichamTerkiba

[6:13:16 PM] HichamTerkiba:
I said Hi opsdroid

[6:13:17 PM] opsdroid:
Hi HichamTerkiba
```


## Message entities

You can also use named format groups to extract entities from the matched message and use them within your skill.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_parse

class MySkill(Skill):
    @match_parse('my name is {name} and my wife is called {wife} and my son is called {son}')
    async def my_name_is(self, message):
        name = message.entities['name']['value']
        wife = message.entities['wife']['value']
        son = message.entities['son']['value']
```


## Field spec

By default parse format captures anything, but format specification can be used to write complex format strings.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_parse

class MySkill(Skill):
    @match_parse('say {text} {num:d} times')
    async def say_n_times(self, message):
        for _ in range(message.entities['num']['value']):
            await message.respond(message.entities['text']['value'])
```

Read [parse format specification](https://github.com/r1chardj0n3s/parse#format-specification) to see all the possibilities.

## Score factor

The parse format parser scores a match based on how long the format string was. It's non-trivial to decide how good a match is against something as basic as a format string, so length is our best proxy.

In case the parse format is too greedy with matches there is also a score factor which defaults to `0.6`. This means a parse format match cannot score higher than `0.6`, however you can use the keyword argument `score_factor` in parse format skills to modify the score calculation.

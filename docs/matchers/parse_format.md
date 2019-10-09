# Parse Format Matcher

## Configuring opsdroid

As in [regex matcher](../matchers/regex.md), in order to enable parse format skills, you must set the `enabled` parameter to true in the parsers section of the opsdroid configuration file.

```yaml
parsers:
  - name: parse_format
    enabled: true
```

## About Parse Format Matcher

This is the simplest matcher available in opsdroid. It matches the message from the user against a string with python [format syntax](https://docs.python.org/3/library/string.html#format-string-syntax). If the string matches then the function is called.

The third party library [parse](https://github.com/r1chardj0n3s/parse) is used to parse the strings.

You can specify which kind of matching you want to apply through the `matching_condition` kwarg (*match* matching is the default). Be careful, the matching condition names are the same than in regex but there are some differences between them.

Matching conditions:

- **match** - Scans through the string looking at the beginning of the string to match the pattern, **but the end must match too**. So if you have `hi` it will match `hi`, but no `say hi` or `hi!`.
- **search** - Scans through the string looking for the first location where the pattern produces a match, and ignores what is before or after the match. So if you have `hi` it will match `hi`, `say hi` or `hi!`.


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

When we run opsdroid and send the message *"hi"* opsdroid will match the hello to the skill and reply immediately. Opsdroid will only trigger the skill if *hi* is the only word in the message.

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


## Message object additional parameters

### `message.parse_result`

You can access any match result from within your skill.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_parse

class MySkill(Skill):
    @match_parse('remember {}')
    async def remember(self, message):
        remember = message.parse_result[0]
        await self.opsdroid.memory.put("remember", remember)
        await message.respond("OK I'll remember that")
```

### Named Fields

Instead of using empty brackets and then access by the position you can assign them a name and access by name.

#### Example 1

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_parse

class MySkill(Skill):
    @match_parse('my name is {} and my wife is called {} and my son is called {}')
    async def my_name_is(self, message):
        name = message.parse_result[0]
        wife = message.parse_result[1]
        son = message.parse_result[2]
```

The above example does not use names and requires knowing the exact order of each of the fields in order to request them by their index.

#### Fixed Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_parse

class MySkill(Skill):
    @match_parse('my name is {name} and my wife is called {wife} and my son is called {son}')
    async def my_name_is(self, message):
        name = message.parse_result['name']
        wife = message.parse_result['wife']
        son = message.parse_result['son']
```

The above example gives each field a name and retrieves each field by using their respective names. This is the recommended approach since it will simplify entity retrieval.


### Field spec

By default parse format captures anything, but format specification can be used to write complex format strings.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_parse

class MySkill(Skill):
    @match_parse('say {text} {num:d} times')
    async def say_n_times(self, message):
        for _ in range(message.parse_result['num']):
            await message.respond(message.parse_result['text'])
```

Read [parse format specification](https://github.com/r1chardj0n3s/parse#format-specification) to see all the possibilities.

## Score factor

As in [regex matcher](../matchers/regex.md), you can use the keyword argument `score_factor` in parse format skills to modify the score calculation.

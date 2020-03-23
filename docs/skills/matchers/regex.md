# Regular Expression

## About Regular Expression Matcher

This matcher matches the message from the user against a [regular expression](https://en.wikipedia.org/wiki/Regular_expression).

You can specify to the regex matcher which kind of matching you want to apply through the `matching_condition` kwarg (*match* matching is the default). This kwarg should give you more control on how to use the regex matcher.

Matching conditions:

- **search** - Scans through the string looking for the first location where the regular expression pattern produces a match.
- **match** - Scans through the string looking at the beginning of the string to match the regular expression pattern.
- **fullmatch** - Scans and checks if the whole string matches the regular expression pattern.

```eval_rst
.. autofunction:: opsdroid.matchers.match_regex
```

### Example 1 - Search condition

Let's use the following hello skill with the kwarg `matching_condition="search"`.

```python
from opsdroid.matchers import match_regex
import random

@match_regex(r'hi|hello|hey|hallo', case_sensitive=False, matching_condition="search")
async def hello(opsdroid, config, message):
    text = random.choice(["Hi {}", "Hello {}", "Hey {}"]).format(message.user)
    await message.respond(text)
```

When we run opsdroid and send the message *"Hi opsdroid"* opsdroid will match the hello to the skill and reply immediately.

```
[6:13:11 PM] HichamTerkiba:
Hi opsdroid

[6:13:12 PM] opsdroid:
Hi HichamTerkiba
```

### Example 2 - match condition

Let's use the following hello skill with the kwarg `matching_condition="match"`.

```python
from opsdroid.matchers import match_regex
import random

@match_regex(r'hi|hello|hey|hallo', case_sensitive=False, matching_condition="match")
async def hello(opsdroid, config, message):
    text = random.choice(["Hi {}", "Hello {}", "Hey {}"]).format(message.user)
    await message.respond(text)
```

With the matching condition kwarg set to match, opsdroid will only trigger the skill if *Hi** is present at the beginning of the message.

```
[6:13:11 PM] HichamTerkiba:
Hi opsdroid

[6:13:12 PM] opsdroid:
Hi HichamTerkiba

[6:13:11 PM] HichamTerkiba:
I said Hi opsdroid

<No reply from opsdroid>
```

### Example 3 - fullmatch condition

Let's use the following hello skill with the kwarg `matching_condition="fullmatch"`.

```python
from opsdroid.matchers import match_regex
import random

@match_regex(r'hi|hello|hey|hallo', case_sensitive=False, matching_condition="fullmatch")
async def hello(opsdroid, config, message):
    text = random.choice(["Hi {}", "Hello {}", "Hey {}"]).format(message.user)
    await message.respond(text)
```
With the matching condition to fullmatch, opsdroid will only trigger the skill if the whole message matches the pattern.

```
[6:13:11 PM] HichamTerkiba:
Hi

[6:13:12 PM] opsdroid:
Hi HichamTerkiba

[6:13:11 PM] HichamTerkiba:
Hi!

<No reply from opsdroid>
```

## Message entities

### Named Groups

Regular expressions may use named groups, which allow you to capture substrings of interest as well as group and structure the regular expression itself. You can give the groups names to retrieve them later.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class MySkill(Skill):
    @match_regex('my name is (?P<name>\w+) and my wife is called (?P<wife>\w+) and my son is called (?P<son>\w+)')
    async def my_name_is(self, message):
        name = message.entities['name']['value']
        wife = message.entities['wife']['value']
        son = message.entities['son']['value']
```

The above example gives each group a name and retrieves each group by using their respective names.  This is the recommended approach to using groups since it will simplify entity retrieval.

## Score factor

The regex parser scores a match based on how long the format string was. It's non-trivial to decide how good a match is against something as basic as a format string, so length is our best proxy.

In case the regular expression is too greedy with matches there is also a score factor which defaults to `0.6`. This means a regex match cannot score higher than `0.6`, however you can use the keyword argument `score_factor` in parse format skills to modify the score calculation.


### Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class MySkill(Skill):
    @match_regex('ping', score_factor=0.9)
    async def ping(self, message):
        await message.respond('pong')
```

In this example, the evaluated score of `ping` skill will be multiplied by `0.9` instead of `0.6`.

# Regular Expression Matcher

## Configuring opsdroid

In order to enable regex skills, you must set the `enabled` parameter to true in the parsers section of the opsdroid configuration file.

If a skill is configured with both the regex and some other NLU matcher then users who don't use NLU will get a simple regex match. However, users with some other NLU configured will get matches on more flexible messages, but they will not see duplicate responses where the regex also matched.

```yaml
parsers:
  regex:
    enabled: true
```

## About Regular Expression Matcher

This is [almost](../matchers/parse_format.md) the simplest matcher available in opsdroid. It matches the message from the user against a regular expression. If the regex matches then the function is called.

You can specify to the regex matcher which kind of matching you want to apply through the `matching_condition` kwarg (*match* matching is the default). This kwarg should give you more control on how to use the regex matcher.

Matching conditions:

- **search** - Scans through the string looking for the first location where the regular expression pattern produces a match.
- **match** - Scans through the string looking at the beginning of the string to match the regular expression pattern.
- **fullmatch** - Scans and checks if the whole string matches the regular expression pattern.

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

## Message object additional parameters

### `message.regex`

You can access any group or wildcard matches in the regex from within your skill.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class MySkill(Skill):
    @match_regex(r'remember (.*)')
    async def remember(self, message):
        remember = message.regex.group(1)
        await self.opsdroid.memory.put("remember", remember)
        await message.respond("OK I'll remember that")
```

### Named Groups

Elaborate regular expressions may use many groups, which allow a developer to capture substrings of interest as well as group and structure the regular expression itself.  It can become difficult to keep track of the multiple groups in complex regular expressions and be unnecessarily complex to include the groups if you refer to them by their index.  Instead, give the groups names to make it easier to keep track of the different groups and retrieve them later.

#### Example 1

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class MySkill(Skill):
    @match_regex('my name is (\w+) and my wife is called (\w+) and my son is called (\w+)')
    async def my_name_is(self, message):
        name = message.regex.group(0)
        wife = message.regex.group(1)
        son = message.regex.group(2)
```

The above example does not use named groups and requires knowing the exact order of each of the groups in order to request them by their index.

#### Fixed Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class MySkill(Skill):
    @match_regex('my name is (?P<name>\w+) and my wife is called (?P<wife>\w+) and my son is called (?P<son>\w+)')
    async def my_name_is(self, message):
        name = message.regex.group('name')
        wife = message.regex.group('wife')
        son = message.regex.group('son')
```

The above example gives each group a name and retrieves each group by using their respective names.  This is the recommended approach to using groups since it will simplify entity retrieval.

## Score factor

In order to make NLU skills execute over regex skills, opsdroid always applies a default factor of `0.6` to every regex evaluated score.

If a developer wants to have a regex skill executed over an NLU one then the keyword argument `score_factor` can be used to achieve this.


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
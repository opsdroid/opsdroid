# Regular Expression Matcher

## Configuring opsdroid

In order to enable regex skills, you must set the `enabled` parameter to true in the parsers section of the opsdroid configuration file.

If a skill is configured with both the regex and some other NLU matcher, users who don't use NLU will get a simple regex match. However, users with some other NLU configured will get matches on more flexible messages, but they will not see duplicate responses where the regex also matched.

```yaml
parsers:
  - name: regex
    enabled: true
```

## About Regular Expression Matcher 

This is the simplest matcher available in opsdroid. It matches the message from the user against a regular expression. If the regex matches, the function is called.

_note: The use of position anchors(`^` or `$`) are encouraged when using regex to match a function. This should prevent opsdroid to be triggered with every use of the matched regular expression_

## Example 1

```python
from opsdroid.matchers import match_regex

@match_regex('hi', case_sensitive=False)
async def hello(opsdroid, config, message):
    await message.respond('Hey')
```

The above skill would be called on any message which matches the regex `'hi'`, `'Hi'`, `'hI'` or `'HI'`. The `case_sensitive` kwarg is optional and defaults to `True`. 

## Example 2

```python
from opsdroid.matchers import match_regex

@match_regex('cold')
async def is_cold(opsdroid, config, message):
    await message.respond('it is')
```

The above skill would be called on any message that matches the regex `'cold'` . 

> user: is it cold?
>
> opsdroid: it is

Undesired effect: 

> user:  Wow, yesterday was so cold at practice!
>
> opsdroid: it is.

Since this matcher searches a message for the regular expression used on a skill, opsdroid will trigger any mention of the `'cold'`. To prevent this position anchors should be used.

#### Fixed example

```python
from opsdroid.matchers import match_regex

@match_regex('cold$')
async def is_cold(opsdroid, config, message):
    await message.respond('it is')
```

Now this skill will only be triggered if `'cold'` is located at the end of the message.

> user: is it cold
>
> opsdroid: it is
>
> user: Wow it was so cold outside yesterday!
>
> opsdroid: 

Since `'cold'` wasn't located at the end of the message, opsdroid didn't react to the second message posted by the user.

## Message object additional parameters

### `message.regex`

A _[re match object](https://docs.python.org/3/library/re.html#re.MatchObject)_ for the regular expression the message was matched against. This allows you to access any wildcard matches in the regex from within your skill.

```python
from opsdroid.matchers import match_regex

@match_regex(r'remember (.*)')
async def remember(opsdroid, config, message):
    remember = message.regex.group(1)
    await opsdroid.memory.put("remember", remember)
    await message.respond("OK I'll remember that")
```

### Named Groups

Elaborate regular expressions may use many groups, both to capture substrings of interest, as well as to group and structure the regular expression itself. In complex regular expressions, it can become difficult to keep track of the various groups and become unecessarily complex to include multiple groups if you refer to them by their index.  Instead, give the groups names to make it easier to keep track of the different groups and retrieve them later. 

#### Example 1

```python
@match_regex('my name is (\w+) and my wife is called (\w+) and my son is called (\w+)')
async def my_name_is(opsdroid, config, message):
    name = message.regex.group(0)
    wife = message.regex.group(1)
    son = message.regex.group(2)
```

The above example does not use named groups and requires knowing the exact order of each of the groups in order to request them by their index.

#### Fixed Example 

```python
@match_regex('my name is (?P<name>\w+) and my wife is called (?P<wife>\w+) and my son is called (?P<son>\w+)')
async def my_name_is(opsdroid, config, message):
    name = message.regex.group('name')
    wife = message.regex.group('wife')
    son = message.regex.group('son')
```

The above example gives each group a name and retrieves each group by using their respective names.  This is the recommended approach to using groups since it will simplify entity retrieval.

## Score factor

In order to make NLU skills execute over regex skills, opsdroid always applies a default factor of `0.6` to every regex evaluated score.

If a developer want to have a regex skill executed over a NLU one, then the keyword argument `score_factor` can be used to achieve this.


### Example 

```python
from opsdroid.matchers import match_regex

@match_regex('ping', score_factor=0.9)
async def ping(opsdroid, config, message):
    await message.respond('pong')
```

In this example, the evaluated score of `ping` skill will be multiplied by `0.9` instead of `0.6`.

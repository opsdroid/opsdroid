# Regular Expression Parser

This is the simplest parser available in opsdroid. It matches the message from the user against a regular expression. If the regex matches the function is called.

## Example

```python
from opsdroid.matchers import match_regex

@match_regex('hi', case_sensitive=False)
async def hello(opsdroid, config, message):
    await message.respond('Hey')
```

The above skill would be called on any message which matches the regex `'hi'`, `'Hi'` or `'HI`. The `case_sensitive` kwarg is optional and defaults to `True`. 

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

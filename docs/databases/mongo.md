# MongoDB

A database module for [opsdroid](https://github.com/opsdroid/opsdroid) to persist memory in a [mongo database](https://www.mongodb.com/).

## Requirements

None.

## Configuration

```yaml
databases:
  mongo:
    host:       "my_host"     # (optional) default "localhost"
    port:       "12345"       # (optional) default "27017"
    database:   "my_database" # (optional) default "opsdroid"
    user:       "my_user"     # (optional)
    password:   "pwd123!"     # (optional)
```

## Usage
This module helps opsdroid to persist memory using an MongoDB database.

## Example
A small change is needed to the [opsdroid's memory feature](../skills/memory.md) example skill in order to use it with the mongo database module:

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex


class RememberSkill(Skill):
    @match_regex(r'remember (.*)')
    async def remember(self, message):
        remember = message.regex.group(1)
        await self.opsdroid.memory.put("remember_this", {"value": remember})
        await message.respond("OK I'll remember that")

    @match_regex(r'remind me')
    async def remind_me(self, message):
        information = await self.opsdroid.memory.get("remember_this")
        await message.respond(information["value"])

    @match_regex(r'forget it')
    async def forget_it(self, message):
        await self.opsdroid.memory.delete("remember_this")
        await message.respond("Ok I'll forget it")
```
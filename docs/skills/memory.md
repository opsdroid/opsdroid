# Memory

opsdroid has a memory class which can be used to persist data between different connectors (which run in different process forks) and between restarts of the application.

## Persisting data

The data can be accessed via the `memory` property of the `opsdroid` pointer which is passed to the skill function. The `memory` object has the following methods.

### `get(key)`

Returns an object from the memory for the key provided.

### `put(key, object)`

Stores the object provided for a specific key.

### `delete(key)`

Deletes the object provided the specific key.

### Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex


class RememberSkill(Skill):
    @match_regex(r'remember (.*)')
    async def remember(self, message):
        remember = message.regex.group(1)
        await self.opsdroid.memory.put("remember_this", remember)
        await message.respond("OK I'll remember that")

    @match_regex(r'remind me')
    async def remind_me(self, message):
        information = await self.opsdroid.memory.get("remember_this")
        await message.respond(information)
        
    @match_regex(r'forget it')
    async def forget_it(self, message):
        await self.opsdroid.memory.delete("remember_this")
        await message.respond("Ok I'll forget it")
```

In the above example we have defined three skill functions. The first takes whatever the user says after the word "remember" and stores it in the database.

The second retrieves and prints out that text when the user says "remind me".

The third deletes what is remembered in the database when the user says "forget it".
## Reference

```eval_rst
.. autoclass:: opsdroid.memory.Memory
    :members:
```

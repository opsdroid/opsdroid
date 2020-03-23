# Memory

opsdroid has a memory class which can be used to persist data between different connectors (which run in different process forks) and between restarts of the application.

## Persisting data

The data can be accessed via the `memory` property of the `opsdroid` pointer which is passed to the skill function. The `memory` object has the following methods.

### `get(key)`

Returns an object from the memory for the key provided.

### `put(key, object)`

Stores the object provided for a specific key.

### Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex


class RememberSkill(Skill):
    @match_regex(r'remember (.*)')
    async def remember(self, message):
        remember = message.regex.group(1)
        await self.opsdroid.memory.put("remember", remember)
        await message.respond("OK I'll remember that")

    @match_regex(r'remind me')
    async def remember(self, message):
        information = await self.opsdroid.memory.get("remember")
        await message.respond(information)
```

In the above example we have defined two skill functions. The first takes whatever the user says after the word "remember" and stores it in the database.

The second retrieves and prints out that text when the user says "remind me".

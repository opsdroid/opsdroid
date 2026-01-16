# Bye Skill

This is a simple example showing how to build a skill in opsdroid that responds with "Goodbye!" when the user types "bye".

## Skill Code

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class ByeSkill(Skill):

    @match_regex(r'bye')
    async def say_goodbye(self, message):
        await message.respond("Goodbye!")
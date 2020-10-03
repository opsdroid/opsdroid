# Catchall

The `catchall` matcher is a special case which is called only when no other skills were matched.

This matcher catches everything - messages and events, if you want to catch only messages you can set the flag `messages_only` to `True`.

It is useful for displaying a help message to the user to show available commands that the bot replies to, for example:

```eval_rst
.. autofunction:: opsdroid.matchers.match_catchall
```

## Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_catchall

class HelpMessageSkill(Skill):
    @match_catchall
    async def help_handler(self, message):
        # Called when no other skills were matched
```

# Always

The `always` matcher is a special case which simply always matches a skill to every single event that passes through opsdroid.

When an event is parsed all skills are ranked by the parsers in order of how confident they are that the message is a match, and then the highest ranking skill is executed. The `always` matcher is useful if you are wanting to do something like keep track of the last time someone spoke, so you need the skill to execute on every message and you will never directly respond to a message.

```eval_rst
.. autofunction:: opsdroid.matchers.match_always
```

## Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_always

class TrackingSkill(Skill):
    @match_always
    async def keep_track(self, message):
        # Put message.user into a database along with a timestamp
```

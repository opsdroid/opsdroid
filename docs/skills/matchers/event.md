# Event

The `event` matcher matches all events of a certain type. It can, for example, be used to write a skill that responds to images or files.

```eval_rst
.. autofunction:: opsdroid.matchers.match_event
```

## Example

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_event
from opsdroid.events import Image, Message

class ShoutyImagesSkill(Skill):
    @match_event(Image)
    async def loudimage(event):
        await event.respond(Message("THAT'S A PRETTY PICTURE"))
```

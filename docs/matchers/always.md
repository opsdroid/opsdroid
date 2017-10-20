# Always matcher

The `always` matcher is a special case which simply always matches a skill to every single message. This is useful if you are wanting to do something like keep track of the last time someone spoke and will probably never directly respond to a message.

## Example

```python
from opsdroid.matchers import match_always

@match_always
async def keep_track(opsdroid, config, message):
    # Put message.user into a database along with a timestamp
```


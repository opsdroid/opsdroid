# Constraints

As well as matchers opsdroid also has constraints. There are decorators for your functions which prevent the skill from being called even if it is matched by a matcher.
You can also invert constraints so that they filter out the opposite of the constraint criteria.

## Constrain rooms

The constraint `constrain_rooms(rooms)` allows you to restrict a skill to a specific set of rooms in your chat client.

### Example

The following skill will respond with 'Hey' if a user says 'hi' in either the `#general` or `#random` rooms but not in `#public`.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
from opsdroid.constraints import constrain_rooms

class MySkill(Skill):
    @match_regex(r'hi')
    @constrain_rooms(['#general', '#random'])
    async def hello(self, message):
        await message.respond('Hey')
```

## Constrain users

The constraint `constrain_users(users)` allows you to restrict a skill to a specific set of users in your chat client.

### Example

The following skill will respond with 'Hey' if the users `alice` or `bob` say 'hi' but not if `charlie` says it.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
from opsdroid.constraints import constrain_users

class MySkill(Skill):
    @match_regex(r'hi')
    @constrain_users(['alice', 'bob'])
    async def hello(self, message):
        await message.respond('Hey')
```

## Constrain connectors

The constraint `constrain_connectors(connectors)` allows you to restrict a skill to a specific connector. Useful if you are configuring opsdroid with more than one connector.

### Example

The following skill will respond with 'Hey' via the `websocket` connector but not the `slack` connector.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
from opsdroid.constraints import constrain_connectors

class MySkill(Skill):
    @match_regex(r'hi')
    @constrain_connectors(['websocket'])
    async def hello(self, message):
        await message.respond('Hey')
```

## Inverting Constraints

It is also possible to invert constraints with the `invert=True` kwarg. This will result in opsdroid filtering
matches based on the **opposite** of the constraint.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex
from opsdroid.constraints import constrain_users

class MySkill(Skill):

    @match_regex(r'hi')
    @constrain_users(['alice', 'bob'], invert=True)
    async def hello(self, message):
        """Says 'Hey' to anyone EXCEPT 'alice' and 'bob'."""
        await message.respond('Hey')
```

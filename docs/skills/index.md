# Skills

Skills are Python functions that you write which describe how the bot should behave when it receives new events.

The simplest skill you can write is a single python file or a directory containing an `__init__.py` file. For example the skill `hello` has a single file called `__init__.py`.

Within this file should be a subclass of `opsdroid.skill.Skill` with methods decorated with an [opsdroid matcher](matchers/index.md) function to let opsdroid know when to trigger the skill. Let's get started with an example.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class HelloSkill(Skill):
    @match_regex(r'hi')
    async def hello(self, message):
        await message.respond('Hey')
```

In this example we are importing the `match_regex` decorator from the opsdroid matchers library. We are then using it to decorate a simple hello world function.

This decorator takes a regular expression to match against the message received from the connector. In this case we are checking to see if the message from the user is "hi".

For more information about the different decorators available in opsdroid see the [matchers documentation](matchers/index.md).

If a message is received and matches the regular expression then the decorated function is called. As arguments opsdroid will pass a Message event object containing information about the message from the user.

```eval_rst
.. note::
   All functions which will be executed should be defined as an `async` function, and calls to functions which may require IO (like a connector or database) should be awaited with the `await` keyword. For more information see [asyncio](https://docs.python.org/3/library/asyncio.html) and [event loops](https://docs.python.org/3/library/asyncio-eventloop.html).
```

To configure opsdroid to use your skill you need to add an entry to the `skills` section of your [configuration](../configuration.md) with the path to your skill file or folder.

```yaml
skills:
  - name: exampleskill
    path: /path/to/my/skill.py
    # Or /path/to/my/skill/ if you created a directory
    # with an __init__.py file in it
```

For more information about the various ways you can package skills and other modules and tell opsdroid about them see the [packaging section](../packaging.md).

It is also possible to specify your expected configuration schema by setting the `CONFIG_SCHEMA` constant within your skill. We use the [voluptuous](https://github.com/alecthomas/voluptuous) library for validating configuration.

```python
from voluptuous import Required

CONFIG_SCHEMA = {
  Required("foo", default="bar"): str,
  Required("baz"): int}
```

By adding this to the top of your skill you are specifying that you expect the user to set `foo` and `baz` in their config. If they fail to specify `foo` it will use the default value of `bar`, but if they fail to specify `baz` the skill will fail to load.

## Matchers

Opsdroid contains a variety of matchers you can use to make use of advanced parsing services such as natural language understanding APIs or non-chat events such as cron based scheduled tasks or webhooks.

```eval_rst
.. toctree::
   :maxdepth: 2

   matchers/index
```

## Constraints

You can also limit how opsdroid matches your skill using constraints. These are like filters for your skills which allow you to say match my skill unless this case is true.

```eval_rst
.. toctree::
   :maxdepth: 2

   constraints
```

## Events

There are many types of events available in opsdroid other than just chat messages. You can trigger skills when new users join a room, when someone is typing, or if someone uploads an image. You can also respond with event types other than chat messages, for example you may want to send an [emoji reaction](https://slack.com/intl/en-gb/help/articles/206870317-use-emoji-reactions) instead.

```eval_rst
.. toctree::
   :maxdepth: 2

   events
```

## Memory

Sometimes you might want to persist information outside of your skill so that it is available after you restart opsdroid. To do this you can use the memory feature in opsdroid to store things in an external database.

```eval_rst
.. toctree::
   :maxdepth: 2

   memory
```

## Start up tasks

You can also specify code to run when your skill is loaded. Perhaps you want to instantiate an API module which will be used by your skills.

```eval_rst
.. toctree::
   :maxdepth: 2

   setup
```

## Helper functions

When you have a skill there will automatically be a pointer to the core opsdroid object. This object has helper functions which enable you to access different things within opsdroid.

For example if you wish to get a pointer to a connector or database object by name you can use the convenience functions.

```python
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex

class HelloSkill(Skill):
    @match_regex(r'hi')
    async def hello(self, message):
        slack = self.opsdroid.get_connector("slack")
        redis = self.opsdroid.get_database("redis")
```

If you try to access a connector or database which has not been configured these functions will return `None.`.

## Examples

For examples of the kind of skills you can build in opsdroid see the [examples section](../examples/index.md). Or continue reading about more of the features you can use to create your skills.

_If you need help or if you are unsure about something join our_ [matrix channel](https://app.element.io/#/room/#opsdroid-general:matrix.org) _and ask away! We are more than happy to help you._

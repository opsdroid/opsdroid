# Creating skills

Like all opsdroid modules skills are installed as a git repository. However skills are designed to be simpler than other modules to ensure that it is easy to get started.

To create a skill you need to create a single python file in your repository with the `__init__.py` name (preferred), or the same name as the skill repository. For example the skill `hello` has a single file called `__init__.py` (could be `hello.py` as well).

Within this file should be functions which are decorated with an opsdroid skill function to let opsdroid know when to trigger the skill. Let's get started with an example.

## Hello world

```python
from opsdroid.matchers import match_regex

@match_regex('hi')
async def hello(opsdroid, config, message):
    await message.respond('Hey')
```

In this example we are importing the `match_regex` decorator from the opsdroid matchers library. We are then using it to decorate a simple hello world function.

This decorator takes a regular expression to match against the message received from the connector. In this case we are checking to see if the message from the user is "hi".

For more information about the different decorators available in opsdroid see the [matchers documentation](../parsers/overview.md).

If the message matches the regular expression then the decorated function is called. As arguments opsdroid will pass a pointer to itself along with a Message object containing information about the message from the user.

To ensure the bot is responsive the concurrency controls introduced in Python 3.5 are used. This means that all functions which will be executed should be defined as an `async` function, and calls to functions which may require IO (like a connector or database) should be awaited with the `await` keyword. For more information see [asyncio](https://docs.python.org/3/library/asyncio.html) and [event loops](https://docs.python.org/3/library/asyncio-eventloop.html).

## Message object

The message object passed to the skill function is an instance of the opsdroid Message class which has the following properties and methods.

Also depending on the parser it may have parser specific properties too. See the [matchers documentation](../parsers/overview.md) for more details.

### `text`

A _string_ containing the message from the user.

### `user`

A _string_ containing the username of the user who wrote the message.

### `room`

A _string_ containing the name of the room or chat channel the message was sent in.

### `connector`

A pointer to the opsdroid _connector object_ which receieved the message.

### `respond(text)`

A method which responds to the message in the same room using the same connector that it was received.

## Persisting data

opsdroid has a memory class which can be used to persist data between different connectors (which run in different process forks) and between restarts of the application.

The data can be accessed via the `memory` property of the `opsdroid` pointer which is passed to the skill function. The `memory` object has the following methods.

### `get(key)`

Returns an object from the memory for the key provided.

### `put(key, object)`

Stores the object provided for a specific key.

### Example

```python
from opsdroid.matchers import match_regex

@match_regex(r'remember (.*)')
async def remember(opsdroid, config, message):
    remember = message.regex.group(1)
    await opsdroid.memory.put("remember", remember)
    await message.respond("OK I'll remember that")

@match_regex(r'remind me')
async def remember(opsdroid, config, message):
    information = await opsdroid.memory.get("remember")
    await message.respond(information)
```

In the above example we have defined two skill functions. The first takes whatever the user says after the work "remember" and stores it in the database.

The second retrieves and prints out that text when the user says "remind me".

## Setup

If your skill requires any setup to be done when opsdroid is started you can create a method simple called `setup` which takes a pointer to opsdroid as it's only argument.

```python
def setup(opsdroid):
  # do some setup stuff here
```

## Example modules

See the following official modules for examples:

 * [hello](https://github.com/opsdroid/skill-hello) - A simple hello world skill.
 * [seen](https://github.com/opsdroid/skill-seen) - Makes use of opsdroid memory.

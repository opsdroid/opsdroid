# Creating skills

Skills are designed to be simpler than other modules to ensure that it is easy to get started.

To create a skill you need to at minimum create a single python file in your repository with the `__init__.py` name. For example the skill `hello` has a single file called `__init__.py`.

Within this file should be functions which are decorated with an opsdroid matcher function to let opsdroid know when to trigger the skill. Let's get started with an example.

## Hello world

```python
from opsdroid.matchers import match_regex

@match_regex(r'hi')
async def hello(opsdroid, config, message):
    await message.respond('Hey')
```

In this example we are importing the `match_regex` decorator from the opsdroid matchers library. We are then using it to decorate a simple hello world function.

This decorator takes a regular expression to match against the message received from the connector. In this case we are checking to see if the message from the user is "hi".

For more information about the different decorators available in opsdroid see the [matchers documentation](../tutorials/introduction.md#matchers-available).

If the message matches the regular expression then the decorated function is called. As arguments opsdroid will pass a pointer to itself along with a Message object containing information about the message from the user.

To ensure the bot is responsive the concurrency controls introduced in Python 3.5 are used. This means that all functions which will be executed should be defined as an `async` function, and calls to functions which may require IO (like a connector or database) should be awaited with the `await` keyword. For more information see [asyncio](https://docs.python.org/3/library/asyncio.html) and [event loops](https://docs.python.org/3/library/asyncio-eventloop.html).

## Message object

The message object passed to the skill function is an instance of the opsdroid `Message` class which has the following properties and methods.

Also depending on the matcher it may have parser specific properties too. See the [matchers documentation](../tutorials/introduction.md#matchers-available) for more details.

### `text`

A _string_ containing the message from the user.

### `user`

A _string_ containing the username of the user who wrote the message.

### `room`

A _string_ containing the name of the room or chat channel the message was sent in.

### `connector`

A pointer to the opsdroid _connector object_ which receieved the message.

### `respond(text, room=None)`

A method which responds to the received message using the same connector.
By default the response is sent to the same room, but arguments may be passed to `connector.respond()` using the `room` argument to change this behaviour, if the connector supports this.

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

In the above example we have defined two skill functions. The first takes whatever the user says after the word "remember" and stores it in the database.

The second retrieves and prints out that text when the user says "remind me".

## Setup

If your skill requires any setup to be done when opsdroid is started you can create a method simple called `setup` which takes a pointer to opsdroid as it's only argument.

```python
def setup(opsdroid):
  # do some setup stuff here
```

## Multiple matchers

It is possible to decorate your function with multiple matchers. There are a couple of reasons why you would want to do this.

### Scheduled skills

You can schedule a skill to run periodically using the crontab matcher. This allows you to decorate your function with a crontab expression which will run your function at that interval.

You can use this in conjunction with other chat based matchers which would allow you to call the function on demand as well as on a schedule.

### Creating public skills with good parser support

You may wish to write a skill which you make publicly available. You will not know which parsers the users of your skill will have enabled and therefore it would be best to support them all.

When a message from a chat client is parsed by opsdroid all skills matching that message are given a score ,either by the NLP API or locally by opsdroid. This score is how confident the NLP service and opsdroid are that the message matches the skill and only the highest scoring skill is executed.

This means that if you decorate a skill with both the `regex` and `dialogflow` matchers then users who don't use Dialogflow will get a simple `regex` match. However users with Dialogflow configured will get matches on more flexible messages, but will not see duplicate responses where the regex also matched.

## Example modules

See the following official modules for examples:

 * [hello](https://github.com/opsdroid/skill-hello) - A simple hello world skill.
 * [seen](https://github.com/opsdroid/skill-seen) - Makes use of opsdroid memory.

*If you need help or if you are unsure about something join our* [gitter channel](https://gitter.im/opsdroid/) *and ask away! We are more than happy to help you.*

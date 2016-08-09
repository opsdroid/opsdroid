# Creating skills

Like all opsdroid modules skills are installed as a git repository. However skills are designed to be simpler than other modules to ensure that it is easy to get started.

To create a skill you need to create a single python file in your repository with the same name as the skill repository. For example the skill `hello` has a single file called `hello.py`.

Within this file should be functions which are decorated with an opsdroid skill function to let opsdroid know when to trigger the skill. Let's get started with an example.

## Hello world

```python
from opsdroid.skills import match_regex

@match_regex('hi')
def hello(opsdroid, message):
    message.respond('Hey')
```

In this example we are importing the `match_regex` decorator from the opsdroid skills library. We are then using it to decorate a simple hello world function.

The decorator takes a regular expression to match against the message received from the connector. In this case we are checking to see if the message from the user is "hi".

If the message matches the regular expression then the decorated function is called. As arguments opsdroid will pass a pointer to itself along with a Message object containing information about the message from the user.

## Message object

The message object passed to the skill function is an instance of the opsdroid Message class which has the following properties and methods.

### `text`

A _string_ containing the message from the user.

### `user`

A _string_ containing the username of the user who wrote the message.

### `room`

A _string_ containing the name of the room or chat channel the message was sent in.

### `regex`

A _[re match object](https://docs.python.org/2/library/re.html#re.MatchObject)_ for the regular expression the message was matched against.

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
from opsdroid.skills import match_regex

@match_regex(r'remember (.*)')
def remember(opsdroid, message):
    remember = message.regex.group(1)
    opsdroid.memory.put("remember", remember)
    message.respond("OK I'll remember that")

@match_regex(r'remind me')
def remember(opsdroid, message):
    message.respond(
      opsdroid.memory.get("remember")
    )
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

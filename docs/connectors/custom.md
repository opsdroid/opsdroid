## Creating a custom connector

Connectors are a class which extends the base opsdroid Connector. The class has three mandatory methods, `connect`, `listen` and `respond`. There are also some default values you can override with the `__init__` function, just be sure you are setting everything that the default init sets.

#### configuration  (property)
*configuration* is a class property of Connector. It's used to access the config parameters of a Connector. This can be used to retrieve specific parameters of a connector from `configuration.yaml`.

#### connect
connect is a method which connects to a specific chat service

### Methods

#### listen
*listen* uses the open connection to the chat service and retrieves messages from it. Each message is formatted into an opsdroid Message object and then parsed. This method should block the thread with an infinite loop but use `await` commands when getting new messages and parsing with opsdroid. This allows the [event loop](https://docs.python.org/3/library/asyncio-eventloop.html) to hand control of the thread to a different function while we are waiting.

#### user_typing
*user_typing* triggers the event message *user is typing* if the connector allows it. This method uses a parameter `trigger` that takes in a boolean value to trigger the event on/off.

#### disconnect
*disconnect* there is also an optional disconnect method that will be called upon shutdown of opsdroid. This can be used to perform any disconnect operations for the connector.


### Handling Events

Opsdroid supports different types of events, which can both be sent and received via connectors, for more information on the different types of events see the [events documentation](../skills/events.md).


Connectors can implement support for sending different types of events using the `opsdroid.connector.register_event` decorator.
This decorator is used to define a method (coroutine) on the connector class for each different event type the connector supports, for instance to add support for `Message` events you may define a method like this:

```python

@register_event(Message)
async def send(self, message):
    await myservice.send(message.text)

```

This method will be called when `Connector.send` is called with a `Message` object as its first argument. Methods such as this can be defined for all event types supported by the connector.

```python

import time

# We recommend you use the official library
# for your chat service and import it here
import chatlibrary

# Import opsdroid dependencies
from opsdroid.connector import Connector, register_event
from opsdroid.events import Message


class MyConnector(Connector):

  def __init__(self, config, opsdroid):
    # Init the config for the connector
    self.name = "MyConnector" # The name of your connector
    self.config = config # The config dictionary to be accessed later
    self.default_target = "MyDefaultRoom" # The default room for messages to go
    self.opsdroid = opsdroid # An instance of opsdroid.core.

  async def connect(self, opsdroid):
    # Create connection object with chat library
    self.connection = await chatlibrary.connect()

  async def listen(self):
    # Listen for new messages from the chat service
    while True:
      # Get raw message from chat
      raw_message = await self.connection.get_next_message()

      # Convert to opsdroid Message object
      #
      # Message objects take a pointer to the connector to
      # allow the skills to call the respond method
      message = Message(raw_message.text, raw_message.user,
                        raw_message.room, self)

      # Parse the message with opsdroid
      await opsdroid.parse(message)

  @register_event(Message)
  async def send(self, message):
    # Send message.text back to the chat service
    await self.connection.send(message.text, message.user,
                               message.target)

  async def disconnect(self):
    # Disconnect from the chat service
    await self.connection.disconnect()

```

---
You might also be interested in reading the [configuration reference - Connector Modules](../configuration.md#connector-modules) in the documentation.
*If you need help or if you are unsure about something join our* [matrix channel](https://app.element.io/#/room/#opsdroid-general:matrix.org) *and ask away! We are more than happy to help you.*

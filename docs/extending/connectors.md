# Creating a connector

Connectors are a class which extends the base opsdroid Connector. The class has three mandatory methods, `connect`, `listen` and `respond`.

#### connect
*connect* is a method which connects to a specific chat service

#### listen
*listen* uses the open connection to the chat service and retrieves messages from it. Each message is formatted into an opsdroid Message object and then parsed. This method should block the thread with an infinite loop but use `await` commands when getting new messages and parsing with opsdroid. This allows the [event loop](https://docs.python.org/3/library/asyncio-eventloop.html) to hand control of the thread to a different function while we are waiting.

#### respond
*respond* will take a Message object and return the contents to the chat service.

```python

import time

# We recommend you use the official library
# for your chat service and import it here
import chatlibrary

# Import opsdroid dependancies
from opsdroid.connector import Connector
from opsdroid.message import Message


class MyConnector(Connector):

  async def connect(self, opsdroid):
    # Create connection object with chat library
    self.connection = await chatlibrary.connect()

  async def listen(self, opsdroid):
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

  async def respond(self, message):
    # Send message.text back to the chat service
    await self.connection.send(raw_message.text, raw_message.user,
                               raw_message.room)

```

# Creating a connector

Connectors are a class which extends the base opsdroid Connector. The class has two mandatory methods, `connect` and `respond`.

#### connect
*connect* is a method which connects to a specific chat service and retrieves messages from it. Each message is formatted into an opsdroid Message object and then parsed. This method should block the thread with an infinite loop.

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

  def connect(self, opsdroid):
    # Create connection object with chat library
    self.connection = chatlibrary.connect()

    while True:
      # Get raw message from chat
      raw_message = self.connection.get_next_message()

      # Convert to opsdroid Message object
      #
      # Message objects take a pointer to the connector to
      # allow the skills to call the respond method
      message = Message(raw_message.text, raw_message.user,
                        raw_message.room, self)

      # Parse the message with opsdroid
      opsdroid.parse(message)

      # Sleep before processing next message
      time.sleep(1)

  def respond(self, message):
    # Send message.text back to the chat service
    self.connection.send(raw_message.text, raw_message.user,
                         raw_message.room)

```

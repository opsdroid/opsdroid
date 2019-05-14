

# Import opsdroid dependencies
from opsdroid.connector import Connector
from opsdroid.events import Message


class MyConnector(Connector):

  def __init__(self, config):
    # Init the config for the connector
    self.name = "" # The name of your connector
    self.config = config # The config dictionary to be accessed later
    self.default_room = "" # The default room for messages to go

  async def connect(self, opsdroid):
    # Create connection object with chat library
    self.connection = await ""

  async def listen(self, opsdroid):
    # Listen for new messages from the chat service
    while True:
      # Get raw message from chat
      raw_message = await ""

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
    await ""

  async def disconnect(self, opsdroid):
    # Disconnect from the chat service
    await ""
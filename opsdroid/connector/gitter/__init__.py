
import logging
import aiohttp





# Import opsdroid dependencies
from opsdroid.connector import Connector
from opsdroid.events import Message

_LOGGER = logging.getLogger(__name__)


class ConnectorGitter(Connector):

  def __init__(self, config, opsdroid=None):
    """Create the connector."""
    super().__init__(config, opsdroid=opsdroid)
    _LOGGER.debug("Starting Gitter connector")
    self.name = "gitter"
    self.accepting_connections = True
    self.session = None
    self.response = None
    self.bot_name = self.config.get("bot-name", 'opsdroid')


  async def connect(self):

    # Create connection object with chat library
    _LOGGER.debug("Connecting with gitter stream")
    self.session = aiohttp.ClientSession()
    self.response = await self.session.get("https://stream.gitter.im/v1/rooms/5a572a4dd73408ce4f87910d/chatMessages?access_token=d404d5500ace6a0ad7b2c0cf9cfc586c80529e30")
    # self.response = yield aiohttp.request('get',"https://stream.gitter.im/v1/rooms/5a572a4dd73408ce4f87910d/chatMessages?access_token=d404d5500ace6a0ad7b2c0cf9cfc586c80529e30")

  async def read_response(self):
    _LOGGER.debug("Connecting with gitter stream")



  async def listen(self):
    _LOGGER.debug("Connecting with gitter stream")
    async for line in self.response.content:
      print(line)

    # Listen for new messages from the chat service




  async def respond(self, message):
    # Send message.text back to the chat service
    await ""

  async def disconnect(self):
    # Disconnect from the chat service
    await ""
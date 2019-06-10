
import logging
import aiohttp
import asyncio
import json
import urllib

from opsdroid.connector import Connector,register_event
from opsdroid.events import Message

_LOGGER = logging.getLogger(__name__)
GITTER_STREAM_API       = "https://stream.gitter.im/v1/rooms"
GITTER_MESSAGE_BASE_API = "https://api.gitter.im/v1/rooms"


class ConnectorGitter(Connector):

  def __init__(self, config, opsdroid=None):
    """Create the connector."""
    super().__init__(config, opsdroid=opsdroid)
    _LOGGER.debug("Starting Gitter connector")
    self.name = "gitter"
    self.session = None
    self.response = None
    self.bot_name = self.config.get("bot-name", 'opsdroid')
    self.room_id = self.config.get("room-id")
    self.access_token = self.config.get("access-token")
    self.update_interval = 1
    self.opsdroid = opsdroid

  async def connect(self):

    # Create connection object with chat library
    _LOGGER.debug("Connecting with gitter stream")
    self.session = aiohttp.ClientSession()
    gitter_url = self.build_url(GITTER_STREAM_API,self.room_id,"chatMessages", access_token = self.access_token)
    _LOGGER.debug("Gitter stream url %s",gitter_url )
    self.response = await self.session.get(gitter_url)

  def build_url(self,base_url , *res, **params):
    url = base_url
    for r in res:
        url = '{}/{}'.format(url, r)
    if params:
        url = '{}?{}'.format(url, urllib.parse.urlencode(params))
    return url

  async def listen(self):
    _LOGGER.debug("Listening with gitter stream")
    while True:
      await asyncio.sleep(self.update_interval)
      async for data in self.response.content.iter_chunked(1024):
        _LOGGER.info(data)
        try:
            data = await self.parse_message(data)
            if data !=None:
              message = Message(
              data["text"],
              data["fromUser"]["username"],
              self.room_id,
              self)
              await self.opsdroid.parse(message)
        except Exception as err:
          _LOGGER.error("Unable to parse message %s", data)
          _LOGGER.error(err.with_traceback())

  async def parse_message(self,message):
    message = message.decode('utf-8').rstrip("\r\n")
    if len(message) > 1:
      message = json.loads(message)
      return message

  @register_event(Message)
  async def send_message(self, message):
    # Send message.text back to the chat service
    url = self.build_url(GITTER_MESSAGE_BASE_API,message.target,"chatMessages")
    headers = {'Authorization': 'Bearer ' + self.access_token, 'Content-Type':'application/json', 'Accept':'application/json'}
    payload = {'text':message.text}
    resp = await self.session.post(url, json=payload, headers=headers)
    if resp.status == 200:
      _LOGGER.debug("Successfully responded")
    else:
      _LOGGER.error("Unable to respond.")

  async def disconnect(self):
    # Disconnect from the chat service
    await self.session.close()


import aiohttp
import asyncio
import logging

from opsdroid.connector import Connector
from opsdroid.message import Message

_LOGGER = logging.getLogger(__name__)
API_PATH = '/api/v1/'


class RocketChat(Connector):
    """A connector for Rocket.chat."""

    def __init__(self, config):
        """Create the connector."""
        super().__init__(config)
        self.name = "rocket.chat"
        self.config = config
        self.default_room = config.get("default-room", "general")
        self.group = config.get("group", None)
        self.url = config.get("channel-url", "https://open.rocket.chat")
        self.latest_update = None
        self.update_interval = config.get("update-interval", 1)

        try:
            self.user_id = config['user-id']
            self.token = config['access-token']
            self.headers = {
                'X-User-Id': self.user_id,
                "X-Auth-Token": self.token
            }
        except (KeyError, AttributeError):
            _LOGGER.error("Unable to login: Access token is missing. "
                          "Rocket.Chat connector will not be available.")

    def build_url(self, method):
        """Build the url to connect with api."""
        return "{}{}{}".format(self.url, API_PATH, method)

    async def connect(self, opsdroid):
        """Connect to the chat service."""
        _LOGGER.info("Connecting to Rocket.Chat")

        async with aiohttp.ClientSession() as session:
            async with session.get(self.build_url('me'),
                                   headers=self.headers) as resp:
                _LOGGER.debug(resp.status)
                if resp.status != 200:
                    _LOGGER.error("Unable to connect.")
                    _LOGGER.error("Rocket.Chat error %s, %s",
                                  resp.status, resp.text)
                else:
                    json = await resp.json()
                    _LOGGER.debug("Connected to Rocket.Chat as %s",
                                  json["username"])

    async def listen(self, opsdroid):
        """Listen to messages in the chat room."""
        while True:
            if self.group:
                url = self.build_url('groups.history?roomName={}'.format(
                    self.group))
            else:
                url = self.build_url('channels.history?roomName={}'.format(
                    self.default_room))

            async with aiohttp.ClientSession() as session:
                params = {}
                if self.latest_update:
                    params['oldest'] = self.latest_update
                async with session.get(url,
                                       params=params,
                                       headers=self.headers) as resp:
                    _LOGGER.debug(resp.status)
                    if resp.status != 200:
                        _LOGGER.error("Rocket.Chat error %s, %s",
                                      resp.status, resp.text)
                    else:
                        json = await resp.json()
                        _LOGGER.debug(json['messages'][0]['msg'])
                        params['oldest'] = json['messages'][0]['_updatedAt']
                        _LOGGER.debug(params)

                        for response in json['messages']:
                            _LOGGER.debug(response['msg'])
                            await opsdroid.parse(response['msg'])

                await asyncio.sleep(self.update_interval)

    async def respond(self, message, room=None):
        """Respond to the user."""
        _LOGGER.debug("Responding with: %s", message.text)
        async with aiohttp.ClientSession() as session:
            data = {}
            data['alias'] = 'opsdroid'
            data['text'] = message.text
            data['avatar'] = ':robot:'
            async with session.post(
                    self.build_url('chat.postMessage?roomName={}'.format(
                        self.group)),
                    headers=self.headers, data=data) as resp:
                # _LOGGER.debug(resp)
                _LOGGER.debug(data)
                if resp.status == 200:
                    _LOGGER.debug('Successfully responded')
                else:
                    _LOGGER.debug("Unable to respond")

  
    async def disconnect(self, opsdroid):
      pass

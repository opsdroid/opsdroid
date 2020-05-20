import re
import logging
import asyncio
import websockets

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message


_LOGGER = logging.getLogger(__name__)


class ConnectorTwitch(Connector):
    """A connector for Twitch."""

    def __init__(self, config, opsdroid=None):
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug(_("Starting Twitch connector."))
        self.name = "twitch"
        self.listening = True
        self._closing = asyncio.Event()
        self.loop = asyncio.get_event_loop()
        self.default_target = config["channel"]
        self.token = config['token']
        self.bot_name = config.get("bot-name", "opsdroid")
        self.websocket = None
        # TODO: Allow usage of SSL connection
        self.server = "ws://irc-ws.chat.twitch.tv"
        self.port = "80"

    async def connect(self):
        """Connect to the chat service"""
        # TODO: Create logic to refresh oauth token - log if token expired.
        # TODO: Call api to trigger specific events such as - gone live
        _LOGGER.info(_("Connecting to Twitch."))

        self.websocket = await websockets.connect(f"{self.server}:{self.port}")
        await self.websocket.send(f"PASS oauth:{self.token}")
        await self.websocket.send(f"NICK {self.bot_name}")
        await self.websocket.send(f"JOIN #{self.default_target}")
     
    async def listen(self):
        message_getter = self.loop.create_task(await self.get_messages_loop())
        await self._closing.wait()
        message_getter.cancel()
   
    async def get_messages_loop(self):
        while self.listening:
            await self._get_messages()
    
    async def _get_messages(self):
        
        resp = await self.websocket.recv()
        _LOGGER.debug(resp)

        chat_message = re.match(r':(?P<user>.*?)!.*?:(?P<message>.*)', resp)
        
        if chat_message:
            message = Message(
                text=chat_message.group("message").rstrip(),
                user=chat_message.group("user"),
                target=f"#{self.default_target}",
                connector=self,
            )
    
            await self.opsdroid.parse(message)
 
    @register_event(Message)
    async def send(self, message):
        """Send message to twitch."""
        await self.websocket.send(f"PRIVMSG #{self.default_target} :{message.text}")

    async def disconnect(self):
        """Disconnect from twitch."""
        # TODO: Figure out why we are getting exception when closing bot
        self.listening = False
        self._closing.set()
        await self.websocket.send(f"PART #{self.default_target}")
        await self.websocket.close()
        await self.websocket.await_close()

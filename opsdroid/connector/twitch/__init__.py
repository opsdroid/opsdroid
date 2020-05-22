import os
import re
import logging
import asyncio
import aiohttp
import websockets
import json

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message

from opsdroid.connector.twitch.events import DeleteMessage, BanUser
from opsdroid.const import TWITCH_API_ENDPOINT, DEFAULT_ROOT_PATH

_LOGGER = logging.getLogger(__name__)
TWITCH_JSON = os.path.join(DEFAULT_ROOT_PATH, 'twitch.json')


def build_api_url(client_id, client_secret, authorization, redirect):
    """Build api url to authenticate and refresh token."""
    clientid = f"?client_id={client_id}"
    secret = f"&client_secret={client_secret}"
    grant = f"&grant_type={authorization}"
    redirect = f"&redirect_uri={redirect}"

    return f"{TWITCH_API_ENDPOINT}{clientid}{secret}{grant}{redirect}"


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
        self.token = None
        self.code = config['code']
        self.client_id = config['client-id']
        self.client_secret = config['client-secret']
        self.redirect = config.get("redirect", "http://localhost")
        self.bot_name = config.get("bot-name", "opsdroid")
        self.websocket = None
        # TODO: Allow usage of SSL connection
        self.server = "ws://irc-ws.chat.twitch.tv"
        self.port = "80"
    
    def save_authentication_data(self, data):
        with open(TWITCH_JSON, 'w') as file:
            json.dump(data, file)
    
    def get_authorization_data(self):
        with open(TWITCH_JSON, 'r') as file:
            data = json.load(file)
            return data
            
    async def request_oauth_token(self):
        """Calls Twitch and requests new oauth token."""
        async with aiohttp.ClientSession() as session:
            code = f"&code={self.code}"
            url = build_api_url(self.client_id, self.client_secret, 'authorization_code', self.redirect) + code

            resp = await session.post(url)
            data = await resp.json()

            self.token = data['access_token']
            self.save_authentication_data(data)
            
    async def refresh_token(self):
        """Attempt to refresh the oauth token."""
        refresh_token = self.get_authorization_data()['refresh_token']
        
        async with aiohttp.ClientSession() as session:
            url = build_api_url(self.client_id, self.client_secret, 'refresh_token', self.redirect) + f"refresh_token={refresh_token}"

            _LOGGER.info(url)
            resp = await session.post(url)
            data = await resp.json()
            
            self.token = data['access_token']
            self.save_authentication_data(data)

    async def connect_websocket(self):
        """Connect to the irc chat through websockets."""
        _LOGGER.info(_("Connecting to Twitch IRC Server."))
        self.websocket = await websockets.connect(f"{self.server}:{self.port}")
        try:
            await self.websocket.send(f"PASS oauth:{self.token}")
        except websockets.ConnectionClosed:
            _LOGGER.info("Oauth token expired. Attempting to refresh token.")
            await self.refresh_token()
            await self.websocket.send(f"PASS oauth:{self.token}")

        await self.websocket.send(f"NICK {self.bot_name}")
        await self.websocket.send(f"JOIN #{self.default_target}")
        await self.websocket.send("CAP REQ :twitch.tv/commands")
        await self.websocket.send("CAP REQ :twitch.tv/tags")
        await self.websocket.send("CAP REQ :twitch.tv/membership")
    
    async def subscribe_webhook(self):
        """Subscribe to Twitch webhooks."""
        # TODO
    
    async def connect(self):
        """Connect to the chat service"""
        # TODO: Call api to trigger specific events such as - gone live
        if not os.path.isfile(TWITCH_JSON):
            _LOGGER.info("No previous authorization data found, requesting new oauth token.")
            await self.request_oauth_token()
        else:
            _LOGGER.info("Found previous authorization data, getting oauth token and attempting to connect.")
            self.token = self.get_authorization_data()['access_token']

        await self.connect_websocket()
    
    async def reconnect(self):
        """Attempt to reconnect to the server."""
        _LOGGER.info("Connection to Twitch dropped. Attempting reconnect...")
        await self.connect()
    
    async def listen(self):
        # TODO: Figure out if we need to this this bit of code since its a websocket.
        # message_getter = self.loop.create_task(await self.get_messages_loop())
        # await self._closing.wait()
        # message_getter.cancel()
        await self.get_messages_loop()
   
    async def get_messages_loop(self):
        while self.listening:
            await self._get_messages()
    
    async def _get_messages(self):
        
        try:
            resp = await self.websocket.recv()
        except websockets.ConnectionClosed:
            await self.reconnect()
            resp = await self.websocket.recv()
        
        _LOGGER.info(f"\n {resp} \n")

        chat_message = re.match(r'@.*;id=(?P<message_id>.*);m.*user-id=(?P<user_id>.*);user-type=.*:(?P<user>.*?)!.*?:(?P<message>.*)', resp)

        if chat_message:
            message = Message(
                text=chat_message.group("message").rstrip(),
                user=chat_message.group("user"),
                user_id=chat_message.group("user_id"),
                raw_event=resp,
                target=f"#{self.default_target}",
                event_id=chat_message.group("message_id"),
                connector=self,
            )
    
            await self.opsdroid.parse(message)
 
    @register_event(Message)
    async def send_message(self, message):
        """Send message to twitch."""
        await self.websocket.send(f"PRIVMSG #{self.default_target} :{message.text}")
    
    @register_event(DeleteMessage)
    async def remove_message(self, event):
        """Send message to twitch."""
        _LOGGER.info(event.id)
        await self.websocket.send(f"PRIVMSG #{self.default_target} :/delete {event.id}")
    
    @register_event(BanUser)
    async def ban_user(self, event):
        """Send message to twitch."""
        await self.websocket.send(f"PRIVMSG #{self.default_target} :/ban {event.user}")

    async def disconnect(self):
        """Disconnect from twitch."""
        # TODO: Figure out why we are getting exception when closing bot
        self.listening = False
        self._closing.set()
        await self.websocket.send(f"PART #{self.default_target}")
        await self.websocket.close()
        await self.websocket.await_close()

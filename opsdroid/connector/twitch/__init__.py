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
from opsdroid.const import TWITCH_API_ENDPOINT, TWITCH_WEBHOOK_ENDPOINT, DEFAULT_ROOT_PATH

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
        self.opsdroid = opsdroid
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
        """Save data obtained from requesting authentication token."""
        with open(TWITCH_JSON, 'w') as file:
            json.dump(data, file)
    
    def get_authorization_data(self):
        """Opens file containing authentication data."""
        with open(TWITCH_JSON, 'r') as file:
            data = json.load(file)
            return data
            
    async def request_oauth_token(self):
        """Calls Twitch and requests new oauth token.
        
        This method assumes that the user already has the code obtained from 
        following the first oauth step which is making a get request to the 
        twitch api endpoint: `https://id.twitch.tv/oauth2/authorize` and passing
        the needed client id, redirect uri and needed scopes to work with the bot.
        
        This method is the second - and final step - when trying to get the oauth token.
        We use the code that the user obtained on step one - check documentation - and
        make a post request to Twitch to get the `access_token` and `refresh_token` so
        we can refresh the access_token when needed. Note that the refresh_token doesn't 
        change with each refresh.
        
        """
        async with aiohttp.ClientSession() as session:
            code = f"&code={self.code}"
            url = build_api_url(self.client_id, self.client_secret, 'authorization_code', self.redirect) + code

            resp = await session.post(url)
            data = await resp.json()

            self.token = data['access_token']
            self.save_authentication_data(data)
            
    async def refresh_token(self):
        """Attempt to refresh the oauth token.
        
        Twitch oauth tokens expire after a day, so we need to do a post request to twitch
        to get a new token when ours expires. The refresh token is already saved on the `twitch.json`
        file so we can just open that file, get the appropriate token and then update the file with the 
        new received data.
        
        """
        refresh_token = self.get_authorization_data()['refresh_token']
        
        async with aiohttp.ClientSession() as session:
            url = build_api_url(self.client_id, self.client_secret, 'refresh_token', self.redirect) + f"&refresh_token={refresh_token}"

            resp = await session.post(url)
            data = await resp.json()
            
            self.token = data['access_token']
            self.save_authentication_data(data)
            
    
    async def send_handshake(self):
        """Send needed data to the websockets to be able to make a connection.
        
        If we try to connect to Twitch with an expired oauth token, we need to 
        request a new token. The problem is that Twitch doesn't close the websocket
        and will only notify the user that the login authentication failed after
        we sent the `PASS`, `NICK` and `JOIN` command to the websocket.
        
        So we need to send the initial commands to Twitch, await for a status with
        `await self.websockets.recv()` and there will be our notification that the 
        authentication failed in the form of `:tmi.twitch.tv NOTICE * :Login authentication failed`
        
        This method was created to prevent us from having to copy the same commands
        and send them to the websocket. If there is an authentication issue, then we
        will have to send the same commands again - just with a new token.
        
        """
        await self.websocket.send(f"PASS oauth:{self.token}")
        await self.websocket.send(f"NICK {self.bot_name}")
        await self.websocket.send(f"JOIN #{self.default_target}")

    async def connect_websocket(self):
        """Connect to the irc chat through websockets.
        
        Our connect method will attempt to make a connection to Twitch through the
        websockets server. If the connection is made, any sort of failure received
        from the websocket will be in the form of a `NOTICE`, unless Twitch closes
        the websocket connection.
        
        In this method we attempt to connect to the websocket and use the previously
        saved oauth token to join a twitch channel. If we get an `authentication failed`
        `NOTICE` we will attempt to refresh the token.
        
        Once we are logged in and on a Twitch channel, we will request access to special
        features from Twitch.
        
        The `commands` request is used to allow us to send special commands to the Twitch
        IRC server.
        
        The `tags` request is used to receive more information with each message received 
        from twitch. Tags enable us to get metadata such as message ids.
        
        The `membership` request is used to get notifications when an user enters the 
        chat server (it doesn't mean that the user is watching the streamer) and also when 
        a user leaves the chat channel.
        
        """
        _LOGGER.info(_("Connecting to Twitch IRC Server."))
        self.websocket = await websockets.connect(f"{self.server}:{self.port}")

        await self.send_handshake()
        status = await self.websocket.recv()
        
        if "authentication failed" in status:
            _LOGGER.info("Oauth token expired, attempting to refresh token.")
            await self.refresh_token()
            await self.send_handshake()

        await self.websocket.send("CAP REQ :twitch.tv/commands")
        await self.websocket.send("CAP REQ :twitch.tv/tags")
        await self.websocket.send("CAP REQ :twitch.tv/membership")
    
    async def subscribe_webhook(self):
        """Subscribe to Twitch webhooks."""
        #TODO
    
    async def connect(self):
        """Connect to Twitch services.
        
        Within our connect method we do a quick check to see if the file `twitch.json` exists in
        the application folder, if this file doesn't exist we assume that it's the first time the
        user is running opsdroid and we do the first request for the oauth token.
        
        If this file exists then we just need to read from the file, get the token in the file and
        attempt to connect to the websockets and subscribe to the Twitch events webhook.
        
        """

        if not os.path.isfile(TWITCH_JSON):
            _LOGGER.info("No previous authorization data found, requesting new oauth token.")
            await self.request_oauth_token()
        else:
            _LOGGER.info("Found previous authorization data, getting oauth token and attempting to connect.")
            self.token = self.get_authorization_data()['access_token']

        await self.connect_websocket()
    
    async def reconnect(self):
        """Attempt to reconnect to the server.
        
        Occasionally the Twitch will send a `RECONNECT` command before closing the connection,
        when this happens we have to connect to the server once more and go through the whole 
        connection process again. This method will simply log a message and call `self.connect()`
        it was created mostly to improve some readibility within the code.
        
        """
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
        """Receive data from websocket connection.
        
        We handle the case where the connection is dropped, if that happens for some
        reason we attempt to reconnect to the websocket service. This method is being
        run through the infinite while loop.
        
        The message that we get from Twitch contains a lot of metadata, so we are using 
        regex named groups to get only the data that we need in order to parse a message
        received.
        
        We also need to check if whatever we received from the websocket is indeed a text
        message that we need to parse, so we use a simple if statement to check if the data
        received matches a text message.
        
        """
        
        try:
            resp = await self.websocket.recv()
        except websockets.ConnectionClosed:
            await self.reconnect()
            resp = await self.websocket.recv()

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
        """Send message to twitch.
        
        This method sends a text message to the chat service. We can't use the
        default `send` method because we are also using different kinds of events
        within this connector.
        
        """
        await self.websocket.send(f"PRIVMSG #{self.default_target} :{message.text}")
    
    @register_event(DeleteMessage)
    async def remove_message(self, event):
        """Remove message from the chat.
        
        This event is used when we need to remove a specific message from the chat 
        service. We need to pass the message id to remove a specific message. So this
        method is calling the `/delete` method together with the message id to remove
        that message.
        
        """
        await self.websocket.send(f"PRIVMSG #{self.default_target} :/delete {event.id}")
    
    @register_event(BanUser)
    async def ban_user(self, event):
        """Ban user from the channel.
        
        This event will be used when we need to ban a specific user from the chat channel.
        Banning a user will also remove all the messages sent by that user, so we don't need
        to worry about removing a lot of mensages.
        
        """
        await self.websocket.send(f"PRIVMSG #{self.default_target} :/ban {event.user}")

    async def disconnect(self):
        """Disconnect from twitch."""
        # TODO: Figure out why we are getting exception when closing bot
        self.listening = False
        self._closing.set()
        await self.websocket.send(f"PART #{self.default_target}")
        await self.websocket.close()
        await self.websocket.await_close()

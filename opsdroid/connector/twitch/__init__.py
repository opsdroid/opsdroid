import os
import re
import logging
import aiohttp
import websockets
import json

from voluptuous import Required

import opsdroid.connector.twitch.events as twitch_event

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message
from opsdroid.const import (
    TWITCH_API_ENDPOINT, 
    TWITCH_WEBHOOK_ENDPOINT, 
    DEFAULT_ROOT_PATH, 
    TWITCH_IRC_MESSAGE_REGEX,
    TWITCH_API_V5_ENDPOINT
    )


CONFIG_SCHEMA = {
    Required("code"): str,
    Required("client-id"): str,
    Required("client-secret"): str,
    Required("channel"): str,
    "redirect": str,
    "forward-url": str,
    "always-listening": bool,
}


_LOGGER = logging.getLogger(__name__)
TWITCH_JSON = os.path.join(DEFAULT_ROOT_PATH, 'twitch.json')


async def get_user_id(channel, token, client_id):
    """Calls twitch api to get broadcaster user id.
    
    A lot of webhooks expect you to pass your user id in order to get the 
    notification when a user subscribes or folllows the broadcaster
    channel.
    
    """
    async with aiohttp.ClientSession() as session:
        response = await session.get("https://api.twitch.tv/helix/users", 
            headers={
                'Authorization': f"Bearer {token}",
                'Client-ID': client_id
            },
            params={
                'login': channel
            })
        
        if response.status >= 400:
            _LOGGER.warning(_("Unable to receive broadcaster id - Error: %s, %s."), response.status, response.message)
        
        response = await response.json()
        
    return response['data'][0]['id']
    


class ConnectorTwitch(Connector):
    """A connector for Twitch."""
    def __init__(self, config, opsdroid=None):
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug(_("Starting Twitch connector."))
        self.name = "twitch"
        self.opsdroid = opsdroid
        self.is_live = config.get("always-listening", False)
        self.default_target = config["channel"]
        self.token = None
        self.code = config['code']
        self.client_id = config['client-id']
        self.client_secret = config['client-secret']
        self.redirect = config.get("redirect", "http://localhost")
        self.bot_name = config.get("bot-name", "opsdroid")
        self.websocket = None
        self.user_id = None
        # TODO: Allow usage of SSL connection
        self.server = "ws://irc-ws.chat.twitch.tv"
        self.port = "80"
        self.forward_url = config['forward-url']

    async def send_message(self, message):
        """Sends message throught websocket.
        
        To send a message to the Twitch IRC server through websocket we need to use the
        same style, we will always send the command `PRIVMSG` and the channel we want to
        send the message to. The message also comes after :.
        
        Args:
            message(string): Text message that should be sent to Twitch chat.
        
        """
        
        await self.websocket.send(f"PRIVMSG #{self.default_target} :{message}")
        

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

            params= {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": 'authorization_code',
                "redirect_uri": self.redirect,
                "code": self.code
            }
            
            resp = await session.post(TWITCH_API_ENDPOINT, params=params)
            data = await resp.json()

            self.token = data['access_token']
            self.save_authentication_data(data)
  
    async def refresh_token(self):
        """Attempt to refresh the oauth token.
        
        Twitch oauth tokens expire after a day, so we need to do a post request to twitch
        to get a new token when ours expires. The refresh token is already saved on the `twitch.json`
        file so we can just open that file, get the appropriate token and then update the file with the 
        new received data.
        
        We are setting our webhook lease to expire after a day as well, so we should subscribe to the webhooks
        again when the oauth token expired since the token expires after a day.
        
        """
        refresh_token = self.get_authorization_data()['refresh_token']
        
        async with aiohttp.ClientSession() as session:
            
            params= {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": 'refresh_token',
                "redirect_uri": self.redirect,
                "refresh_token": refresh_token
            }
            
            resp = await session.post(TWITCH_API_ENDPOINT, params=params)
            data = await resp.json()
            
            self.token = data['access_token']
            self.save_authentication_data(data)
        
        await self.webhook('follows', 'subscribe')
        await self.webhook('stream changed', 'subscribe')

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
            _LOGGER.info(_("Oauth token expired, attempting to refresh token."))
            await self.refresh_token()
            await self.send_handshake()

        await self.websocket.send("CAP REQ :twitch.tv/commands")
        await self.websocket.send("CAP REQ :twitch.tv/tags")
        await self.websocket.send("CAP REQ :twitch.tv/membership")
    
    async def webhook(self, topic, mode):
        """Subscribe to a specific webhook.
        
        Twitch has different webhooks that you can subscribe to, when you subscribe to a
        particular webhook, a `post` request needs to be made containing a `JSON` payload,
        that tells Twitch what subscription you are attempting to do. 
        
        When you submit the `post` request to `TWITCH_WEBHOOK_ENDPOINT`, twitch will send back
        a `get` request to your `callback` url (`hub.callback`) with a challenge. Twitch will 
        then await for a response containing only the challenge in plain text.
        
        With this in mind, that is the reason why we open two routes (`get` and `post`) that link 
        to `/connector/<connector name>`.
        
        The `hub.topic` represents the webhook that we want to suscribe from twitch.
        The `hub.lease_seconds` defines the number of seconds until the subscription expires, maximum
        is 864000 seconds (10 days), but we will set up a day as our expiration since our app oauth 
        tokens seem to expire after a day.
        
        Args:
            topic (string): Twitch webhook url to subscribe/unsubscribe to.
            mode (string): subscribe or unsuscribe to the webhook.
        
        """
        _LOGGER.info(_("Attempting to connect to webhook %s."), topic)
        
        if topic == 'follows':
            topic = f"https://api.twitch.tv/helix/users/follows?to_id={self.user_id}&first=1"
        
        if topic == 'stream changed':
            topic = f"https://api.twitch.tv/helix/streams?user_id={self.user_id}"
        
        if topic == "subscribers":
            topic = f"https://api.twitch.tv/helix/subscriptions/events?broadcaster_id={self.user_id}&first=1"

        headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.token}"}
        
        async with aiohttp.ClientSession() as session:
            
            payload = {
                "hub.callback": f"{self.forward_url}/connector/{self.name}", 
                "hub.mode": mode,
                "hub.topic": topic,
                "hub.lease_seconds": 60 * 60 * 24,
            }
            
            response = await session.post(
                TWITCH_WEBHOOK_ENDPOINT, 
                headers=headers, 
                json=payload
            )
            
            if response.status >= 400:

                _LOGGER.debug(_('Error: %s - %s'), response.status, response.message)

    async def handle_challenge(self, request):
        """Challenge handler for get request made by Twitch.
        
        Upon subscription to a Twitch webhook, Twitch will do a get request to the 
        `callback` url provided to check if the url exists. Twitch will do a get request
        with a challenge and expects the `callback` url to return that challenge in plain-text
        back to Twitch.
        
        This is what we are doing here, we are getting `hub.challenge` from the request and return
        it in plain-text, if we can't find that challenge we will return a status code 500.
        
        Args:
            request (aiohttp.web.Request): Request made to the get route created for webhook subscription.
        
        Returns:
           aiohttp.web.Response: if request contains `hub.challenge` we return it, otherwise return status 500.
        
        """
        challenge = request.rel_url.query.get('hub.challenge')

        if challenge:
            return aiohttp.web.Response(text=challenge)
        
        _LOGGER.debug(_("Failed to get challenge from GET Request made by Twitch."))
        return aiohttp.web.Response(status=500)

    async def twitch_webhook_handler(self, request):
        """Handle event from Twitch webhooks.
        
        This method will handle events when they are pushed to the webhook post route. Each webhook will
        send a different kind of payload so we can handle each event and trigger the right opsdroid event
        for the received payload.
        
        For follow events the payload will contain `from_id`(broadcaster id), `from_username`(broadcaster username)
        `to_id`(follower id), `to_name` (follower name) and `followed_at` (timestamp).
        
        For stream changes a lot more things are returned but we only really care about `type`(if live/offline), 
        `title`(stream title).
        
        For subscriptions events we will want to know `event_type`, `timestamp`, `event_data.plan_name`, `event_data.is_gift`,
        `event_data.tier`, `event_data.username` and `event_data.gifter_name`.
        
        Args:
            request (aiohttp.web.Request): Request made to the post route created for webhook subscription.

        Return:
            aiohttp.web.Response: Send a `received` message and status 200 - Twitch will keep sending the event if 
            it doesn't get the 200 status code. 

        """
        payload = await request.json()
        [data] = payload.get('data')
        
        _LOGGER.info(_("Got event from Twitch - %s") % data)

        try:
            if data.get('followed_at'):
                _LOGGER.debug(_("Follower event received by Twitch."))
                user_followed = twitch_event.UserFollowed(
                    follower = data['from_name'],
                    followed_at = data['followed_at'],
                    connector=self,
                )
                await self.opsdroid.parse(user_followed)
            
            if data.get('started_at'):
                _LOGGER.debug(_("Broadcaster went live event received by Twitch."))
                self.is_live = True
                await self.connect_websocket()
                
                stream_started = twitch_event.StreamStarted(
                    title = data['title'],
                    viewer = data['viewer_count'],
                    started_at = data['started_at'],
                    connector = self
                )
                
                await self.opsdroid.parse(stream_started)
            
            if data.get('event_type') == "subscriptions.notification":
                _LOGGER.debug(_("Subscriber event received by Twitch."))
                user_subscription = twitch_event.UserSubscribed(
                    username=data['event_data']['user_name'],
                    message=data['event_data']['message']
                )
                
                await self.opsdroid.parse(user_subscription)
            
            if data.get('event_type') == "subscriptions.subscribe":
                _LOGGER.debug(_("Subscriber event received by Twitch."))
                user_subscription = twitch_event.UserSubscribed(
                    username=data['event_data']['user_name'],
                    message=None
                )
                
                await self.opsdroid.parse(user_subscription)
            
            if data.get('event_type') == "subscriptions.subscribe" and data['event_data'].get('is_gift'):
                _LOGGER.debug(_("Gifted subscriber event received by Twitch."))
                gifted_subscription = twitch_event.UserGiftedSubscription(
                    gifter_name=data['event_data']['gifter_name'],
                    gifted_named=data['event_data']['user_name']
                )
                
                await self.opsdroid.parse(gifted_subscription)
               
        except KeyError:
            if not payload.get('data'):
                # When the stream goes offline, Twitch will return `data: []`
                # if data is none we assume the streamer whent offline
                stream_ended = twitch_event.StreamEnded(connector=self)
                await self.opsdroid.parse(stream_ended)
                
                if not self.config.get("always-listening"):
                    self.is_live = False
                    self.disconnect_websockets()

        return aiohttp.web.Response(text=json.dumps("Received"), status=200)

    async def connect(self):
        """Connect to Twitch services.
        
        Within our connect method we do a quick check to see if the file `twitch.json` exists in
        the application folder, if this file doesn't exist we assume that it's the first time the
        user is running opsdroid and we do the first request for the oauth token.
        
        If this file exists then we just need to read from the file, get the token in the file and
        attempt to connect to the websockets and subscribe to the Twitch events webhook.
        
        """
        if not os.path.isfile(TWITCH_JSON):
            _LOGGER.info(_("No previous authorization data found, requesting new oauth token."))
            await self.request_oauth_token()
        else:
            _LOGGER.info(_("Found previous authorization data, getting oauth token and attempting to connect."))
            self.token = self.get_authorization_data()['access_token']
        
        self.user_id = await get_user_id(self.default_target, self.token, self.client_id)
        
        # Setup routes for webhooks subscription
        self.opsdroid.web_server.web_app.router.add_get(
            f"/connector/{self.name}", self.handle_challenge
        )
        self.opsdroid.web_server.web_app.router.add_post(
            f"/connector/{self.name}", self.twitch_webhook_handler
        )
        
        await self.webhook('follows', 'subscribe')
        await self.webhook('stream changed', 'subscribe')
        await self.webhook('subscribers', 'subscribe')
        
        if self.is_live:
            await self.connect_websocket()

    async def reconnect(self):
        """Attempt to reconnect to the server.
        
        Occasionally the Twitch will send a `RECONNECT` command before closing the connection,
        when this happens we have to connect to the server once more and go through the whole 
        connection process again.
        
        So if the websocket connection drops we will call the `self.connect_websocket` method
        to attempt to reconnect to the websocket.
        
        """
        if self.is_live:
            _LOGGER.debug(_("Connection to Twitch dropped. Attempting reconnect..."))
            await self.connect_websocket()

    async def listen(self):
        """Listen method of the connector.

        Every connector has to implement the listen method. When an
        infinite loop is running, it becomes hard to cancel this task.
        So we are creating a task and set it on a variable so we can
        cancel the task.

        """
        await self.get_messages_loop()

    async def get_messages_loop(self):
        """Listen for and parse events."""
        while self.is_live:
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
            return
        else:
            resp = await self.websocket.recv()

        chat_message = re.match(TWITCH_IRC_MESSAGE_REGEX, resp)

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
    async def _send_message(self, message):
        """Send message to twitch.
        
        This method sends a text message to the chat service. We can't use the
        default `send` method because we are also using different kinds of events
        within this connector.
        
        """
        await self.send_message(message.text)

    @register_event(twitch_event.DeleteMessage)
    async def remove_message(self, event):
        """Remove message from the chat.
        
        This event is used when we need to remove a specific message from the chat 
        service. We need to pass the message id to remove a specific message. So this
        method is calling the `/delete` method together with the message id to remove
        that message.
        
        """
        await self.send_message(f"/delete {event.id}")

    @register_event(twitch_event.BanUser)
    async def ban_user(self, event):
        """Ban user from the channel.
        
        This event will be used when we need to ban a specific user from the chat channel.
        Banning a user will also remove all the messages sent by that user, so we don't need
        to worry about removing a lot of mensages.
        
        """
        await self.send_message(f"/ban {event.user}")

    @register_event(twitch_event.CreateClip)
    async def create_clip(self):
        """Create clip from broadcast.
        
        We send a post request to twitch to create a clip from the broadcast, Twitch will
        return a response containing a clip `id` and `edit_url`. TWitch mentions that the
        way to check if the clip was created successfully is by making a `get` request
        to the `clips` API enpoint and query by the `id` obtained from the previous 
        request.
        
        """
        async with aiohttp.ClientSession() as session:
            headers = {"Client-ID": self.client_id, "Authorization": f"Bearer {self.token}"}
            resp = await session.post(
                f"https://api.twitch.tv/helix/clips?broadcaster_id={self.user_id}",
                headers=headers
            )
            response = await resp.json()

            clip_data = await session.get(
                f"https://api.twitch.tv/helix/clips?id={response['data'][0]['id']}",
                headers=headers
            )
            
            if clip_data.status == 200:
                resp = await clip_data.json()
                [data] = resp.get('data')
                
                _LOGGER.debug(_("Twitch clip created successfully."))
            
                await self.send_message(data['embed_url'])
                
                return
            _LOGGER.debug(_("Failed to create Twitch clip %s"), response)

    @register_event(twitch_event.UpdateTitle)
    async def update_stream_title(self, event):
        """Update Twitch title.
        
        To update your channel details you need to use Twitch API V5(kraken). The so called "New Twitch API"
        doesn't have an enpoint to update the channel. To update your channel details you need to do a put
        request and pass your title into the url. 
        
        Args:
            event (twitch.events.UpdateTitle): opsdroid event containing `status` (your title). 

        """
        async with aiohttp.ClientSession() as session:
            headers = {
                "Client-ID": self.client_id, 
                "Authorization": f"OAuth {self.token}",
                "Accept": "application/vnd.twitchtv.v5+json"
            
            }
            
            param = {"channel[status]": event.status}
            resp = await session.put(
                f"{TWITCH_API_V5_ENDPOINT}/channels/{self.user_id}",
                headers=headers,
                params=param
            )
            
            if resp.status == 200:
                _LOGGER.debug(_("Twitch channel title updated to %s"), event.status)
                
                return

            _LOGGER.debug(_("Failed to update Twitch channel title. Error %s - %s"), resp.status, resp.message)

    async def disconnect_websockets(self):
        """Disconnect from the websocket."""
        await self.websocket.send(f"PART #{self.default_target}")
        await self.websocket.close()
        await self.websocket.await_close()
    
    async def disconnect(self):
        """Disconnect from twitch.
        
        Before opsdroid exists we will want to disconnect the Twitch connector, we need to
        do some clean up. We first set the while loop flag to False to stop the loop and then
        try to unsubscribe from all the webhooks that we subscribed to on connect - we want to
        do that because when we start opsdroid and the `connect` method is called we will send 
        another subscribe request to Twitch. After we will send a `PART` command to leave the 
        channel that we joined on connect.
        
        Finally we try to close the websocket connection.
        
        """
        if self.is_live:
            await self.disconnect_websockets()
        self.is_live = False
        await self.webhook('follows', 'unsubscribe')
        await self.webhook('stream changed', 'unsubscribe')
        await self.webhook('subscribers', 'unsubscribe')

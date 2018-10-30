"""A connector for Twitter."""
import json
import logging

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy import API
from tweepy.streaming import StreamListener

from opsdroid.connector import Connector
from opsdroid.message import Message


_LOGGER = logging.getLogger(__name__)


class StdOutListener(StreamListener):
    """A listener for handing activity in the twitter stream."""

    def __init__(self, api, opsdroid, connector):
        """Construct the listener."""
        super().__init__(api)
        self.opsdroid = opsdroid
        self.connector = connector

    def on_connect(self):
        """On connecting to Twitter."""
        _LOGGER.debug("Connected to Twitter.")
        self.connector.connected = True

    def on_disconnect(self, notice):
        """On disconnecting from Twitter."""
        _LOGGER.debug("Connection lost: %s", notice)
        self.connector.connected = False

    def on_data(self, raw_data):
        """On receive data from Twitter."""
        _LOGGER.debug("Processing tweet.")
        status = json.loads(raw_data)
        tweet_screen_name = status["direct_message"]["sender"]["screen_name"]
        if self.connector.config.get("enable_dms", False) and \
                "direct_message" in status and \
                "sender" in status["direct_message"] and \
                tweet_screen_name != self.connector.screen_name:
            self.connector.process_direct_message(status["direct_message"])

        if self.connector.config.get("enable_tweets", False) and \
                all([k in status for k in [
                        "created_at",
                        "id",
                        "text",
                        "user"
                ]]) and \
                status["user"]["screen_name"] != self.connector.screen_name:
            self.connector.process_tweet(status)

        return True

    @staticmethod
    def on_error(status_code):
        """On error from Twitter."""
        _LOGGER.error(status_code)


class ConnectorTwitter(Connector):
    """A connector for Twitter."""

    def __init__(self, config):
        """Construct the connector."""
        logging.debug("Loaded twitter connector")
        super().__init__(config)
        self.name = "twitter"
        self.screen_name = None
        self.config = config
        self.opsdroid = None
        self.api = None
        self.stream = None
        self.connected = False
        self.listen_task = None
        try:
            self.auth = OAuthHandler(self.config["consumer_key"],
                                     self.config["consumer_secret"])
            self.auth.secure = True
            self.auth.set_access_token(self.config["oauth_token"],
                                       self.config["oauth_token_secret"])
        except KeyError:
            _LOGGER.error("Missing auth tokens!")

    async def connect(self, opsdroid):
        """Connect to Twitter."""
        _LOGGER.debug("Connecting to twitter")
        self.opsdroid = opsdroid
        self.api = API(self.auth)
        self.screen_name = self.api.me().name
        _LOGGER.debug(self.screen_name)

    async def disconnect(self, opsdroid):
        """Disconnect from Twitter."""
        self.stream.disconnect()

    async def listen(self, opsdroid):
        """Listen for new message."""
        self.stream = Stream(self.auth,
                             StdOutListener(self.api, opsdroid, self))
        self.listen_task = opsdroid.eventloop.run_in_executor(
            None, self.stream.userstream)
        await self.listen_task

    def clean_tweet(self, tweet):
        """Clean up the tweet text."""
        return tweet.replace("@{}".format(self.screen_name), '').strip()

    def process_tweet(self, tweet):
        """Create a Message from a tweet json and parse it."""
        _LOGGER.debug("Processing tweet")
        _LOGGER.debug(tweet)
        tweet["text"] = self.clean_tweet(tweet["text"])
        message = Message(tweet["text"],
                          tweet["user"]["screen_name"],
                          {"type": "tweet", "id": tweet["id"]},
                          self)
        self.opsdroid.eventloop.create_task(self.opsdroid.parse(message))

    def process_direct_message(self, direct_message):
        """Create a Message from a tweet json and parse it."""
        _LOGGER.debug("Processing direct message")
        _LOGGER.debug(direct_message)
        room = {"type": "direct_message", "id": direct_message["id"]}
        message = Message(direct_message["text"],
                          direct_message["sender"]["screen_name"],
                          room,
                          self)
        self.opsdroid.eventloop.create_task(self.opsdroid.parse(message))

    async def respond(self, message, room=None):
        """Respond with a message."""
        _LOGGER.debug("Responding via twitter")
        _LOGGER.debug(message.user)
        _LOGGER.debug(message.text)
        if message.room["type"] == "direct_message":
            self.api.send_direct_message(screen_name=message.user,
                                         text=message.text)
        if message.room["type"] == "tweet":
            room_id = message.room["id"]
            if message.user is None:
                self.api.update_status(status=message.text)
            else:
                if "id" in message.room:
                    self.api.update_status(status=message.text,
                                           in_reply_to_status_id=room_id)
                else:
                    tweet = "@{} {}".format(message.user, message.text)
                    self.api.update_status(status=tweet)

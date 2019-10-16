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

    def __init__(self, opsdroid, connector):
        self.tweetCount = 0
        self.opsdroid = opsdroid
        self.connector = connector

    def on_connect(self):
        _LOGGER.debug("Connection established!!")

    def on_disconnect(self, notice):
        _LOGGER.debug("Connection lost!! : ", notice)

    def on_data(self, status):
        _LOGGER.debug("Processing tweet.")
        status = json.loads(status)
        if self.connector.config.get("enable_dms", False) and \
                "direct_message" in status and \
                "sender" in status["direct_message"] and \
                status["direct_message"]["sender"]["screen_name"] != self.connector.screen_name:
            self.connector.process_dm(status["direct_message"])

        if self.connector.config.get("enable_tweets", False) and \
                "created_at" in status and \
                "id" in status and \
                "text" in status and \
                "user" in status and \
                status["user"]["screen_name"] != self.connector.screen_name:
            self.connector.process_tweet(status)

        return True

    def on_error(self, status):
        print(status)


class ConnectorTwitter(Connector):

    def __init__(self, config):
        """Setup the connector."""
        logging.debug("Loaded twitter connector")
        super().__init__(config)
        self.name = "twitter"
        self.screen_name = None
        self.config = config
        self.opsdroid = None
        try:
            self.auth = OAuthHandler(self.config["consumer_key"],
                                     self.config["consumer_secret"])
            self.auth.secure = True
            self.auth.set_access_token(self.config["oauth_token"],
                                       self.config["oauth_token_secret"])
        except KeyError as e:
            _LOGGER.error("Missing auth tokens!")

    async def connect(self, opsdroid):
        """Connect to twitter."""
        _LOGGER.debug("Connecting to twitter")
        self.opsdroid = opsdroid
        self.api = API(self.auth)
        self.screen_name = self.api.me().name
        _LOGGER.debug(self.screen_name)

    async def listen(self, opsdroid):
        """Listen for new message."""
        self.stream = Stream(self.auth, StdOutListener(opsdroid, self))
        opsdroid.eventloop.run_in_executor(None, self.stream.userstream)

    def clean_tweet(self, tweet):
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

    def process_dm(self, dm):
        """Create a Message from a tweet json and parse it."""
        _LOGGER.debug("Processing direct message")
        _LOGGER.debug(dm)
        message = Message(dm["text"],
                          dm["sender"]["screen_name"],
                          {"type": "dm", "id": dm["id"]},
                          self)
        self.opsdroid.eventloop.create_task(self.opsdroid.parse(message))

    async def respond(self, message, room=None):
        """Respond with a message."""
        _LOGGER.debug("Responding via twitter")
        _LOGGER.debug(message.user)
        _LOGGER.debug(message.text)
        if message.room["type"] == "dm":
            self.api.send_direct_message(screen_name=message.user,
                                         text=message.text)
        if message.room["type"] == "tweet":
            if message.user is None:
                self.api.update_status(status=message.text)
            else:
                if "id" in message.room:
                    self.api.update_status(status=message.text,
                                           in_reply_to_status_id=message.room["id"])
                else:
                    tweet = "@{} {}".format(message.user, message.text)
                    self.api.update_status(status=tweet)
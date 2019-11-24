"""A connector for Mattermost."""
import logging
import json

from mattermostdriver import Driver, Websocket
from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    Required("token"): str,
    Required("url"): str,
    Required("team-name"): str,
    "scheme": str,
    "port": int,
    "ssl-verify": bool,
    "connect-timeout": int,
}


class ConnectorMattermost(Connector):
    """A connector for Mattermost."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug(_("Starting Mattermost connector"))
        self.name = "mattermost"
        self.token = config["token"]
        self.url = config["url"]
        self.team_name = config["team-name"]
        self.scheme = config.get("scheme", "https")
        self.port = config.get("port", 8065)
        self.verify = config.get("ssl-verify", True)
        self.timeout = config.get("connect-timeout", 30)
        self.request_timeout = None
        self.mfa_token = None
        self.debug = False
        self.listening = True

        self.mm_driver = Driver(
            {
                "url": self.url,
                "token": self.token,
                "scheme": self.scheme,
                "port": self.port,
                "verify": self.verify,
                "timeout": self.timeout,
                "request_timeout": self.request_timeout,
                "mfa_token": self.mfa_token,
                "debug": self.debug,
            }
        )

    async def connect(self):
        """Connect to the chat service."""
        _LOGGER.info(_("Connecting to Mattermost"))

        login_response = self.mm_driver.login()

        _LOGGER.info(login_response)

        if "id" in login_response:
            self.bot_id = login_response["id"]
        if "username" in login_response:
            self.bot_name = login_response["username"]

        _LOGGER.info(_("Connected as %s"), self.bot_name)

        self.mm_driver.websocket = Websocket(
            self.mm_driver.options, self.mm_driver.client.token
        )

        _LOGGER.info(_("Connected successfully"))

    async def disconnect(self):
        """Disconnect from Mattermost."""
        self.listening = False
        self.mm_driver.logout()

    async def listen(self):
        """Listen for and parse new messages."""
        await self.mm_driver.websocket.connect(self.process_message)

    async def process_message(self, raw_message):
        """Process a raw message and pass it to the parser."""
        _LOGGER.info(raw_message)

        message = json.loads(raw_message)

        if "event" in message and message["event"] == "posted":
            data = message["data"]
            post = json.loads(data["post"])
            await self.opsdroid.parse(
                Message(
                    post["message"],
                    data["sender_name"],
                    data["channel_name"],
                    self,
                    raw_event=message,
                )
            )

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug(
            _("Responding with: '%s' in room  %s"), message.text, message.target
        )
        channel_id = self.mm_driver.channels.get_channel_by_name_and_team_name(
            self.team_name, message.target
        )["id"]
        self.mm_driver.posts.create_post(
            options={"channel_id": channel_id, "message": message.text}
        )

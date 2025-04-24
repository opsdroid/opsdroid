"""A connector for Mattermost."""
import logging
import json

from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message

from .driver import Driver

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    Required("token"): str,
    Required("url"): str,
    Required("team-name"): str,
    "use-threads": bool,
    "scheme": str,
    "port": int,
    "connect-timeout": int,
}


class ConnectorMattermost(Connector):
    """A connector for Mattermost."""

    def __init__(self, config, opsdroid=None):
        """Create the connector."""
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug(_("Starting Mattermost connector"))
        self.name = config.get("name", "mattermost")
        self._token = config["token"]
        self._url = config["url"]
        self._team_name = config["team-name"]
        self._scheme = config.get("scheme", "https")
        self._port = config.get("port", 8065)
        self._timeout = config.get("connect-timeout", 30)
        self._use_threads = config.get("use-threads", False)

        self._bot_id = None

        self._mm_driver = Driver(
            {
                "url": self._url,
                "token": self._token,
                "scheme": self._scheme,
                "port": self._port,
                "timeout": self._timeout,
            }
        )
        self._websocket = None

    async def connect(self):
        """Connect to the chat service. This does not include the Websocket!"""
        _LOGGER.info(_("Connecting to Mattermost"))

        await self._mm_driver.__aenter__()
        try:
            login_response = await self._mm_driver.connect()
        except Exception as ex:
            _LOGGER.error(_("Failed connecting to Mattermost '%s'"), ex)
            raise ex

        body = await login_response.json()
        _LOGGER.info(
            _("Mattermost responded with the identity of the token's user: '%s'"),
            repr(body),
        )

        if "id" not in body:
            raise ValueError(
                "Mattermost response must contain our own client ID. Otherwise OpsDroid would respond to itself indefinitely."
            )
        self._bot_id = body["id"]

        if "username" in body:
            _LOGGER.info(_("Connected as %s"), body["username"])

        _LOGGER.info(_("Connected successfully"))

    async def disconnect(self):
        """Disconnect from Mattermost."""
        await self._mm_driver.__aexit__(None, None, None)

    async def listen(self):
        """
        Listen for and parse new messages.
        This is only the Websocket and must be called after 'connect', since that initializes the driver/web client
        """
        self._websocket = self._mm_driver.init_websocket(self.process_message)
        await self._websocket

    async def process_message(self, raw_json_message):
        """Process a raw message and pass it to the parser."""
        _LOGGER.debug(
            _("Processing raw Mattermost message: '%s'"), repr(raw_json_message)
        )

        if "event" in raw_json_message and raw_json_message["event"] == "posted":
            data = raw_json_message["data"]
            post = json.loads(data["post"])
            # if connected to Mattermost, don't parse our own messages
            # (https://github.com/opsdroid/opsdroid/issues/1775)
            if self._bot_id != post["user_id"]:
                await self.opsdroid.parse(
                    Message(
                        text=post["message"],
                        user=data["sender_name"],
                        target=data["channel_name"],
                        connector=self,
                        raw_event=raw_json_message,
                    )
                )

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug(
            _("Responding with: '%s' in room  %s"), message.text, message.target
        )

        async with self._mm_driver.channels.get_channel_for_team_by_name(
            self._team_name, message.target
        ) as response:
            myjson = await response.json()
            channel_id = myjson["id"]

        body = {}
        if self._use_threads:
            data = message.linked_event.raw_event["data"]
            post = json.loads(data["post"])

            # root_id is set if it is already a thread
            # otherwise use the id to start a new thread from that top level message
            root_id = ("root_id" in post and post["root_id"]) or post["id"]

            body = {
                "channel_id": channel_id,
                "message": message.text,
                "root_id": root_id,
            }
        else:
            body = {"channel_id": channel_id, "message": message.text}

        async with self._mm_driver.posts.create_post(json=body) as response:
            _LOGGER.debug(
                _("Mattermost responds with status code '%s' to the new post"),
                response.status,
            )

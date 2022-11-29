"""A connector for Discord."""
import logging
from .client import DiscordClient

from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message

_LOGGER = logging.getLogger(__name__)
_DISCORD_SEND_URL = "https://discord.com/api"
CONFIG_SCHEMA = {
    Required("token"): str,
    "bot-name": str,
}


class ConnectorDiscord(Connector):
    """A connector for Discord"""
    def __init__(self, config, opsdroid=None):
        """Create the connector.
        Args:
            config (dict): configuration settings from the
                file config.yaml.
            opsdroid (OpsDroid): An instance of opsdroid.core.
        """
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug("Starting Discord Connector.")
        self.name = config.get("name", "discord")
        self.bot_name = config.get("bot-name", "opsdroid")
        self.token = config.get("token")
        self.client = DiscordClient(self.handle_message, self.rename)
        self.bot_id = None
    
    async def rename(self):
        if self.bot_name != self.client.user.name :
            await self.client.user.edit(username=self.bot_name)

    async def handle_message(self, text, user, user_id, target, msg):
        """
        Handle messages received from discord gateway. All the arguments are provided by the 
        """
        event = Message(
            text=text,
            user=user,
            user_id=user_id,
            target=target,
            connector=self,
            raw_event=msg,
        )
        _LOGGER.info(user + " said " + text)
        await self.opsdroid.parse(event)

    async def connect(self):
        await self.client.start(self.token)

    async def listen(self):
        """Listen handled by webhooks."""
        pass


    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug(_("Responding to Discord."))
        await message.target.send(message.text)

    async def disconnect(self):
        _LOGGER.debug(_("Discord Client disconnecting"))
        self.client.close()


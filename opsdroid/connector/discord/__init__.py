"""A connector for Discord."""
import logging
import io
import aiohttp

from .client import DiscordClient, discordMessage, discordFile

from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message,File,Image

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
        self.client = DiscordClient(self.rename, self.handle_message, self.handle_image ,self.handle_file)
        self.bot_id = None
    
    async def rename(self):
        """
        Rename the bot if bot-name changed
        """
        if self.bot_name != self.client.user.name :
            await self.client.user.edit(username=self.bot_name)

    async def handle_message(self, message:discordMessage):
        """
        Handle messages received from discord gateway. For now, it can be text message, file or an image
        """
        event = Message(text=message.content, user=message.author.name, user_id=message.author.id, target=message.channel, connector=self, raw_event=message)
        _LOGGER.info(message.author.name + " said " + message.content)
        await self.opsdroid.parse(event)
    
    async def handle_image(self, message:discordMessage, img_nb:int):
        image = message.attachments[img_nb]
        event = Image(url=image.url, name=image.filename ,user=message.author.name, user_id=message.author.id, target=message.channel, connector=self,raw_event=message, event_id=img_nb)
        _LOGGER.info(message.author.name+" sent the image at "+image.url)
        await self.opsdroid.parse(event)

    async def handle_file(self, message:discordMessage, file_nb:int):
        file = message.attachments[file_nb]
        event = File(url=file.url, name=file.filename, user=message.author.name, user_id=message.author.id, target=message.channel, connector=self,raw_event=message, event_id=file_nb)
        _LOGGER.info(message.author.name+" sent the file at "+file.url)
        await self.opsdroid.parse(event)
    
    @register_event(Image)
    async def send_image(self, image_event:Image):
        """Send image to Discord."""
        _LOGGER.debug(_("Sending image to Discord."))
        data = io.BytesIO(await image_event.get_file_bytes())
        await image_event.target.send(file=discordFile(data, image_event.name))

    @register_event(File)
    async def send_file(self, file_event:File):
        """Send file to Discord."""
        _LOGGER.debug(_("Sending file to Discord."))
        data = io.BytesIO(await file_event.get_file_bytes())
        await file_event.target.send(file=discordFile(fp=data, filename=file_event.name))


    async def connect(self):
        """Connect to the discord gateway to get messages sent to the bot"""
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
        """Disconnect from the client (so the bot appears offline)"""
        _LOGGER.debug(_("Discord Client disconnecting"))
        self.client.close()


import logging
_LOGGER = logging.getLogger(__name__)
import discord
from discord import Message as discordMessage
from discord import File as discordFile


class DiscordClient(discord.Client):
    """
    subclass of discord.Client
    It is used according to the discord library
    """
    def __init__(self, rename_func, handle_message_func, handle_image_func, handle_file_func):
        intents = discord.Intents(messages=True, message_content=True)
        super().__init__(intents=intents)
        self.rename_func = rename_func
        self.handle_message_func = handle_message_func
        self.handle_image_func = handle_image_func
        self.handle_file_func = handle_file_func
        discord.utils.setup_logging( 
                level=_LOGGER.level, # same level of login as opsdroid
                root=False,
            )
    
    async def on_ready(self):
        """When the bot is ready online, this function is activated"""
        _LOGGER.debug('Logged in as '+str(self.user.name)+" "+str(self.user.id))
        await self.rename_func() # we rename according to the name given in bot-name

    async def on_message(self, message:discordMessage):
        """When the bot receive a message"""
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return
        else :
            # we use the function given in parameter of the class
            await self.handle_message_func(message)
             # we test if a file is attached
            if (len(message.attachments) > 0):
                for i in range(len(message.attachments)):
                    file = message.attachments[i]
                    # then we test if one of the attached files is an image
                    if file.filename.endswith(('.jpg','.jpeg','.png')):
                        await self.handle_image_func(message, i)
                    else :
                        await self.handle_file_func(message, i)
            
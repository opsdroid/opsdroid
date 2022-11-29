import logging
_LOGGER = logging.getLogger(__name__)
import discord


class DiscordClient(discord.Client):

    def __init__(self, handle_message_func, rename_func):
        intents = discord.Intents(messages=True, message_content=True)
        super().__init__(intents=intents)
        self.handle_message_func = handle_message_func
        self.rename_func = rename_func
        discord.utils.setup_logging(
                level=_LOGGER.level,
                root=False,
            )
    
    async def on_ready(self):
        _LOGGER.debug('Logged in as '+str(self.user.name)+" "+str(self.user.id))
        await self.rename_func()

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return
        else :
            await self.handle_message_func(message.content, message.author.name, message.author.id, message.channel, message)
            
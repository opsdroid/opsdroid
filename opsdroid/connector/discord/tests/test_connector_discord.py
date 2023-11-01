import asyncio
import asynctest
from unittest.mock import AsyncMock
from opsdroid.connector.discord import ConnectorDiscord
from opsdroid.connector.discord.client import DiscordClient

# from opsdroid.events import Message

# In order to test the discord connector, a mock bot has been created alongside an opsdroid bot
# The mock bot will send messages to the opsdroid bot in order to test the bot.
# We assume that the discord library is already tested and reliable.

# Fill in with a token of a discord bot
test_token = ""


class TestConnector(ConnectorDiscord):
    def __init__(self, config, opsdroid=None):
        super().__init__(config, opsdroid)
        self.client = AsyncMock(DiscordClient(self.rename, self.handle_message, self.handle_image ,self.handle_file))


class Test(asynctest.TestCase):
    def test_init(self, opsdroid=None):
        connector = ConnectorDiscord({}, opsdroid)
        self.assertIsNone(connector.default_target)
        self.assertEqual(connector.name, "discord")
        self.assertEqual(connector.bot_name, "opsdroid")
        config = {"name": "toto", "bot-name": "bot", "token": test_token}
        connector = ConnectorDiscord(config, opsdroid)
        self.assertEqual(connector.name, "toto")
        self.assertEqual(connector.bot_name, "bot")
        self.assertEqual(connector.token, test_token)

    async def test_connect(self, opsdroid=None):
        connector = TestConnector({"token": test_token}, opsdroid)
        await connector.connect()
        connector.client.start.assert_called()
    
    async def test_rename(self,opsdroid=None):
        """connector = TestConnector({"bot-name":"botNewName","token":test_token},opsdroid)
        await connector.connect()
        connector.client.user.edit.assert_called()"""
        pass

    async def test_handle_message(self,opsdroid=None):
        """connector = TestConnector({"token": test_token},opsdroid)
        with self.assertLogs() as log:
            await connector.handle_message(msg)
        self.assertEqual(len(log.records),1)
        self.assertEqual(log.records[0],"user said hello")
        connector.opsdroid.parse.assert_called()"""
        pass
    
    async def test_send_message(self,opsdroid=None):
        """connector = TestConnector({"token": test_token},opsdroid)
        message = Message("hello","user","1","target")
        message.target.send = asynctest.Mock()
        with self.assertLogs(level="DEBUG") as log:
            await connector.send_message(message)
        self.assertEqual(log.records[0],"Responding to Discord.")
        message.target.send.assert_called_with(message.text)"""
        pass
    
    async def test_disconnect(self,opsdroid=None):
        """connector = TestConnector({"token": test_token},opsdroid)
        await connector.connect()
        with self.assertLogs(level="DEBUG") as log:
            await connector.disconnect()
        print(log.output[0])
        self.assertEqual("DEBUG:opsdroid.connector.discord:Discord Client disconnecting",log.output[0])
        connector.client.close.assert_called()"""
        pass
    
    async def test_on_ready(self,opsdroid=None):
        """connector = TestConnector({"token": test_token},opsdroid)
        with self.assertLogs(level="DEBUG") as log:
            await connector.client.on_ready()
        self.assertEqual("DEBUG:opsdroid.connector.discord:Logged in as "
                         + str(connector.client.user.name)+" "+str(connector.client.user.id),
                         log.output[0])
        connector.client.rename_func.assert_called()"""
        pass

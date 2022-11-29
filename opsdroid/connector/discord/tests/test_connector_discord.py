import asynctest
from opsdroid.connector.discord import ConnectorDiscord
from opsdroid.connector.discord.client import DiscordClient

# from opsdroid.events import Message

# In order to test the discord connector, a mock bot has been created alongside an opsdroid bot
# The mock bot will send messages to the opsdroid bot in order to test the bot.
# We assume that the discord library is already tested and reliable.

test_token = ""


class TestConnector(ConnectorDiscord):
    def __init__(self, config, opsdroid=None):
        super().__init__(config, opsdroid)
        self.client = asynctest.Mock(DiscordClient(self.handle_message, self.rename))


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

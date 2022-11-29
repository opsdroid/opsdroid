# import logging
import pytest
import asynctest
import asyncio

from opsdroid.connector.discord import ConnectorDiscord

# from opsdroid.events import Message

# In order to test the discord connector, a mock bot has been created alongside an opsdroid bot
# The mock bot will send messages to the opsdroid bot in order to test the bot.
# Both bots have been added to a test server.
# We assume that the discord library is already tested and reliable.


mock_token = "MTA0NzEwMDk1MTYwNzExNTgxNg.G3EhiS.MK2r2dORN5ScI9q4TQ2Ikz9v8Ns7tq7mSw_4uE"
test_token = "MTA0NzEwNTM5ODQ1NDM3NDQ4MA.GtMN0U.VnQneacG6dWpKr4fM0f0s0tdujqQsJRkX0B5f8"

class Test(asynctest.TestCase):
    def test_init(self,opsdroid=None):
        connector =asynctest.Mock(ConnectorDiscord({}, opsdroid))
        self.assertIsNone(connector.default_target)
        self.assertEqual(connector.name, "discord")
        self.assertEqual(connector.bot_name, "opsdroid")
        config = {"name":"toto",
                    "bot-name":"bot",
                    "token":test_token}
        connector = asynctest.Mock(ConnectorDiscord(config,opsdroid))
        self.assertEqual(connector.name, "toto")
        self.assertEqual(connector.bot_name, "bot")
        self.assertEqual(connector.token,test_token)
    
    async def test_connect(self,opsdroid=None):

        connector = asynctest.Mock(ConnectorDiscord({"token": test_token}, opsdroid))
        connector.connect()
        connector.client.start.assert_called()   
    async def test_discord_handle_message(self,opsdroid):
        """Test the new discord message handler."""

    

@pytest.mark.asyncio


@pytest.mark.asyncio
async def test_discord_message_handler_invalid(opsdroid, caplog):
    """Test the new discord message handler for invalid message."""
    import aiohttp

    connector = ConnectorDiscord({}, opsdroid=opsdroid)
    req_ob = {
        "object": "page",
        "entry": [{"messaging": [{"message": {"text": "Hello"}, "sender": {}}]}],
    }
    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = req_ob

    connector.opsdroid = opsdroid
    connector.opsdroid.parse = amock.CoroutineMock()

    response = await connector.discord_message_handler(mock_request)
    assert not connector.opsdroid.parse.called
    assert "Unable to process message." in caplog.text
    assert isinstance(response, aiohttp.web.Response)
    assert response.status == 200


@pytest.mark.asyncio
async def test_discord_challenge_handler(opsdroid):
    """Test the discord challenge handler."""
    import aiohttp

    connector = ConnectorDiscord({"verify-token": "token_123"}, opsdroid=opsdroid)
    mock_request = amock.Mock()
    mock_request.query = {
        "hub.verify_token": "token_123",
        "hub.challenge": "challenge_123",
    }

    response = await connector.discord_challenge_handler(mock_request)
    assert isinstance(response, aiohttp.web.Response)
    assert response.text == "challenge_123"
    assert response.status == 200

    mock_request.query = {
        "hub.verify_token": "token_abc",
        "hub.challenge": "challenge_123",
    }
    response = await connector.discord_challenge_handler(mock_request)
    assert isinstance(response, aiohttp.web.Response)
    assert response.status == 403


@pytest.mark.asyncio
async def test_listen(opsdroid):
    """Test that listen does nothing."""
    connector = ConnectorDiscord({}, opsdroid=opsdroid)
    await connector.listen()
    assert True  # Listen should not block and return immediately


@pytest.mark.asyncio
async def test_respond(opsdroid):
    """Test that responding sends a message."""
    post_response = amock.Mock()
    post_response.status = 200

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request:
        assert opsdroid.__class__.instances
        connector = ConnectorDiscord({}, opsdroid=opsdroid)
        room = "a146f52c-548a-11e8-a7d1-28cfe949e12d"
        test_message = Message(
            text="Hello world", user="Alice", target=room, connector=connector
        )
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)
        await test_message.respond("Response")
        assert patched_request.called


@pytest.mark.asyncio
async def test_respond_bad_response(opsdroid):
    """Test that responding sends a message and get bad response."""
    post_response = amock.Mock()
    post_response.status = 401
    post_response.text = amock.CoroutineMock()
    post_response.text.return_value = "Error"

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request:
        assert opsdroid.__class__.instances
        connector = ConnectorDiscord({}, opsdroid=opsdroid)
        room = "a146f52c-548a-11e8-a7d1-28cfe949e12d"
        test_message = Message(
            text="Hello world", user="Alice", target=room, connector=connector
        )
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(post_response)
        await test_message.respond("Response")
        assert patched_request.called
        assert post_response.text.called

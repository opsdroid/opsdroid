"""Tests for the ConnectorSlack class."""
import asyncio

import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.connector.slack import ConnectorSlack
from opsdroid.message import Message


class TestConnectorSlack(unittest.TestCase):
    """Test the opsdroid Slack connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorSlack({"api-token": "abc123"})
        self.assertEqual("#general", connector.default_room)
        self.assertEqual("slack", connector.name)

    def test_missing_api_key(self):
        """Test that creating without an API key raises an error."""
        with self.assertRaises(KeyError):
            ConnectorSlack({})

    # def test_connect(self):
    #     connector = ConnectorSlack({})
    #     with self.assertRaises(NotImplementedError):
    #         self.loop.run_until_complete(connector.connect({}))

    # def test_listen(self):
    #     connector = ConnectorSlack({})
    #     with self.assertRaises(NotImplementedError):
    #         self.loop.run_until_complete(connector.listen({}))

    # def test_respond(self):
    #     connector = ConnectorSlack({})
    #     with self.assertRaises(NotImplementedError):
    #         self.loop.run_until_complete(connector.respond({}))

    # def test_react(self):
    #     connector = ConnectorSlack({})
    #     reacted = self.loop.run_until_complete(connector.react({}, 'emoji'))
    #     self.assertFalse(reacted)

    # def test_user_typing(self):
    #     opsdroid = 'opsdroid'
    #     connector = ConnectorSlack({})
    #     user_typing = self.loop.run_until_complete(
    #         connector.user_typing(opsdroid, trigger=True))
    #     assert user_typing is None


class TestConnectorSlackAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid Slack connector class."""

    async def test_lookup_username(self):
        """Test that looking up a username works and that it caches."""
        connector = ConnectorSlack({"api-token": "abc123"})
        connector.slacker.users.info = amock.CoroutineMock()
        mock_user = mock.Mock()
        mock_user.body = {"user": {"name" : "testuser"}}
        connector.slacker.users.info.return_value = mock_user

        self.assertEqual(len(connector.known_users), 0)

        await connector.lookup_username('testuser')
        self.assertTrue(len(connector.known_users), 1)
        self.assertTrue(connector.slacker.users.info.called)

        connector.slacker.users.info.reset_mock()
        await connector.lookup_username('testuser')
        self.assertEqual(len(connector.known_users), 1)
        self.assertFalse(connector.slacker.users.info.called)

        with self.assertRaises(ValueError):
            mock_user.body = {"user": None}
            connector.slacker.users.info.return_value = mock_user
            await connector.lookup_username('invaliduser')


    async def test_respond(self):
        connector = ConnectorSlack({"api-token": "abc123"})
        connector.slacker.chat.post_message = amock.CoroutineMock()
        await connector.respond(Message("test", "user", "room", connector))
        self.assertTrue(connector.slacker.chat.post_message.called)

    async def test_reconnect(self):
        connector = ConnectorSlack({"api-token": "abc123"})
        connector.connect = amock.CoroutineMock()
        with amock.patch('asyncio.sleep') as mocked_sleep:
            await connector.reconnect(10)
            self.assertTrue(connector.connect.called)
            self.assertTrue(mocked_sleep.called)

"""Tests for the ConnectorMattermost class."""
import json

import pytest
from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, Mock

from opsdroid.core import OpsDroid
from opsdroid.connector.mattermost import ConnectorMattermost
from opsdroid.cli.start import configure_lang
from opsdroid.events import Message


pytestmark = pytest.mark.anyio


class TestConnectorMattermostAsync(TestCase):
    """Test the async methods of the opsdroid Mattermost connector class."""

    async def setUp(self):
        configure_lang({})

    async def test_missing_api_key(self):
        """Test that creating without an API key raises an error."""
        with self.assertRaises(KeyError):
            ConnectorMattermost({}, opsdroid=OpsDroid())

    async def test_connect(self):
        connector = ConnectorMattermost(
            {
                "token": "abc123",
                "url": "localhost",
                "team-name": "opsdroid",
                "scheme": "http",
            },
            opsdroid=OpsDroid(),
        )
        opsdroid = AsyncMock()
        opsdroid.eventloop = self.loop
        connector.mm_driver.login = MagicMock()
        connector.mm_driver.login.return_value = {"id": "1", "username": "opsdroid_bot"}
        await connector.connect()
        self.assertEqual("1", connector.bot_id)
        self.assertEqual("opsdroid_bot", connector.bot_name)
        self.assertEqual("mattermost", connector.name)
        self.assertEqual(30, connector.timeout)

    async def test_disconnect(self):
        connector = ConnectorMattermost(
            {
                "token": "abc123",
                "url": "localhost",
                "team-name": "opsdroid",
                "scheme": "http",
            },
            opsdroid=OpsDroid(),
        )
        opsdroid = AsyncMock()
        opsdroid.eventloop = self.loop
        connector.mm_driver.login = MagicMock()
        connector.mm_driver.login.return_value = {"id": "1", "username": "opsdroid_bot"}
        connector.mm_driver.logout = MagicMock()
        await connector.connect()
        await connector.disconnect()
        self.assertTrue(connector.mm_driver.logout.called)

    async def test_listen(self):
        """Test that listening consumes from the socket."""
        connector = ConnectorMattermost(
            {
                "token": "abc123",
                "url": "localhost",
                "team-name": "opsdroid",
                "scheme": "http",
            },
            opsdroid=OpsDroid(),
        )
        connector.mm_driver.websocket = Mock()
        connector.mm_driver.websocket.connect = AsyncMock()
        await connector.listen()

    async def test_process_message(self):
        """Test processing a mattermost message."""
        connector = ConnectorMattermost(
            {
                "token": "abc123",
                "url": "localhost",
                "team-name": "opsdroid",
                "scheme": "http",
            },
            opsdroid=OpsDroid(),
        )
        connector.opsdroid = AsyncMock()
        connector.opsdroid.parse = AsyncMock()

        post = json.dumps(
            {
                "id": "wr9wetwc87bgdcx6opkjaxwb6a",
                "create_at": 1574001673419,
                "update_at": 1574001673419,
                "edit_at": 0,
                "delete_at": 0,
                "is_pinned": False,
                "user_id": "mrtopue9oigr8poa3bgfq4if4a",
                "channel_id": "hdnm8gbxfp8bmcns7oswmwur4r",
                "root_id": "",
                "parent_id": "",
                "original_id": "",
                "message": "hello",
                "type": "",
                "props": {},
                "hashtags": "",
                "pending_post_id": "mrtopue9oigr8poa3bgfq4if4a:1574001673362",
                "metadata": {},
            }
        )

        message = json.dumps(
            {
                "event": "posted",
                "data": {
                    "channel_display_name": "@daniccan",
                    "channel_name": "546qd6zsyffcfcafd77a3kdadr__mrtopue9oigr8poa3bgfq4if4a",
                    "channel_type": "D",
                    "mentions": '["546qd6zsyffcfcafd77a3kdadr"]',
                    "post": post,
                    "sender_name": "@daniccan",
                    "team_id": "",
                },
                "broadcast": {
                    "omit_users": "",
                    "user_id": "",
                    "channel_id": "hdnm8gbxfp8bmcns7oswmwur4r",
                    "team_id": "",
                },
                "seq": 3,
            }
        )
        await connector.process_message(message)
        self.assertTrue(connector.opsdroid.parse.called)

    async def test_do_not_process_own_message(self):
        """Test that we do not process our own messages when connected to Mattermost."""
        connector = ConnectorMattermost(
            {
                "token": "abc123",
                "url": "localhost",
                "team-name": "opsdroid",
                "scheme": "http",
            },
            opsdroid=OpsDroid(),
        )
        opsdroid = AsyncMock()
        opsdroid.eventloop = self.loop
        connector.mm_driver.login = MagicMock()
        connector.mm_driver.login.return_value = {"id": "1", "username": "opsdroid_bot"}
        await connector.connect()
        self.assertEqual("1", connector.bot_id)
        self.assertEqual("opsdroid_bot", connector.bot_name)

        connector.opsdroid = AsyncMock()
        connector.opsdroid.eventloop = self.loop
        connector.opsdroid.parse = AsyncMock()

        post = json.dumps(
            {
                "id": "wr9wetwc87bgdcx6opkjaxwb7b",
                "create_at": 1574001673420,
                "update_at": 1574001673420,
                "edit_at": 0,
                "delete_at": 0,
                "is_pinned": False,
                "user_id": "1",
                "channel_id": "hdnm8gbxfp8bmcns7oswmwur4r",
                "root_id": "",
                "parent_id": "",
                "original_id": "",
                "message": "hello",
                "type": "",
                "props": {},
                "hashtags": "",
                "pending_post_id": "mrtopue9oigr8poa3bgfq4if4a:1574001673372",
                "metadata": {},
            }
        )

        message = json.dumps(
            {
                "event": "posted",
                "data": {
                    "channel_display_name": "@daniccan",
                    "channel_name": "546qd6zsyffcfcafd77a3kdadr__mrtopue9oigr8poa3bgfq4if4a",
                    "channel_type": "D",
                    "mentions": '["546qd6zsyffcfcafd77a3kdadr"]',
                    "post": post,
                    "sender_name": "@opsdroid_bot",
                    "team_id": "",
                },
                "broadcast": {
                    "omit_users": "",
                    "user_id": "",
                    "channel_id": "hdnm8gbxfp8bmcns7oswmwur4r",
                    "team_id": "",
                },
                "seq": 4,
            }
        )
        await connector.process_message(message)
        self.assertFalse(connector.opsdroid.parse.called)

    async def test_send_message(self):
        connector = ConnectorMattermost(
            {
                "token": "abc123",
                "url": "localhost",
                "team-name": "opsdroid",
                "scheme": "http",
            },
            opsdroid=OpsDroid(),
        )
        connector.mm_driver = Mock()
        connector.mm_driver.channels = Mock()
        connector.mm_driver.channels.get_channel_by_name_and_team_name = MagicMock()
        connector.mm_driver.posts = Mock()
        connector.mm_driver.posts.create_post = MagicMock()
        await connector.send(
            Message(text="test", user="user", target="room", connector=connector)
        )
        self.assertTrue(connector.mm_driver.channels.get_channel_by_name_and_team_name)
        self.assertTrue(connector.mm_driver.posts.create_post.called)

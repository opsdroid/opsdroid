"""Tests for the RocketChat class."""

import os.path

import asyncio
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.connector.github import ConnectorGitHub
from opsdroid.events import Message


class TestConnectorGitHub(unittest.TestCase):
    """Test the opsdroid github connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorGitHub({"name": "github", "token": "test"})
        self.assertEqual(None, connector.default_target)
        self.assertEqual("github", connector.name)

    def test_missing_token(self):
        """Test that attempt to connect without info raises an error."""
        ConnectorGitHub({})
        self.assertLogs("_LOGGER", "error")


class TestConnectorGitHubAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid github connector class."""

    def setUp(self):
        opsdroid = amock.CoroutineMock()
        configure_lang({})
        self.connector = ConnectorGitHub(
            {"name": "github", "token": "test"}, opsdroid=opsdroid
        )

    async def test_connect(self):
        with amock.patch("aiohttp.ClientSession.get") as patched_request:
            mockresponse = amock.CoroutineMock()
            mockresponse.status = 200
            mockresponse.json = amock.CoroutineMock(return_value={"login": "opsdroid"})
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(mockresponse)
            await self.connector.connect()
            self.assertEqual(self.connector.github_username, "opsdroid")
            self.assertTrue(
                self.connector.opsdroid.web_server.web_app.router.add_post.called
            )

    async def test_connect_failure(self):
        result = amock.MagicMock()
        result.status = 401

        with OpsDroid() as opsdroid, amock.patch(
            "aiohttp.ClientSession.get"
        ) as patched_request:

            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)

            await self.connector.connect()
            self.assertLogs("_LOGGER", "error")

    async def test_disconnect(self):
        self.assertEqual(await self.connector.disconnect(), None)

    async def test_get_comment(self):
        """Test a comment create event creates a message and parses it."""
        with open(
            os.path.join(
                os.path.dirname(__file__), "responses", "github_comment_payload.json"
            ),
            "r",
        ) as f:
            mock_request = amock.CoroutineMock()
            mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
            self.connector.opsdroid = amock.CoroutineMock()
            self.connector.opsdroid.parse = amock.CoroutineMock()
            await self.connector.github_message_handler(mock_request)
            message = self.connector.opsdroid.parse.call_args[0][0]
            self.assertEqual(message.connector.name, "github")
            self.assertEqual(message.text, "hello")
            self.assertEqual(message.target, "opsdroid/opsdroid#237")
            self.assertTrue(self.connector.opsdroid.parse.called)

    async def test_get_pr(self):
        """Test a PR create event creates a message and parses it."""
        with open(
            os.path.join(
                os.path.dirname(__file__), "responses", "github_pr_payload.json"
            ),
            "r",
        ) as f:
            mock_request = amock.CoroutineMock()
            mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
            self.connector.opsdroid = amock.CoroutineMock()
            self.connector.opsdroid.parse = amock.CoroutineMock()
            await self.connector.github_message_handler(mock_request)
            message = self.connector.opsdroid.parse.call_args[0][0]
            self.assertEqual(message.connector.name, "github")
            self.assertEqual(message.text, "hello world")
            self.assertEqual(message.target, "opsdroid/opsdroid-audio#175")
            self.assertTrue(self.connector.opsdroid.parse.called)

    async def test_get_issue(self):
        """Test an issue create event creates a message and parses it."""
        with open(
            os.path.join(
                os.path.dirname(__file__), "responses", "github_issue_payload.json"
            ),
            "r",
        ) as f:
            mock_request = amock.CoroutineMock()
            mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
            self.connector.opsdroid = amock.CoroutineMock()
            self.connector.opsdroid.parse = amock.CoroutineMock()
            await self.connector.github_message_handler(mock_request)
            message = self.connector.opsdroid.parse.call_args[0][0]
            self.assertEqual(message.connector.name, "github")
            self.assertEqual(message.text, "test")
            self.assertEqual(message.target, "opsdroid/opsdroid#740")
            self.assertTrue(self.connector.opsdroid.parse.called)

    async def test_get_label(self):
        """Test a label create event doesn't create a message and parse it."""
        with open(
            os.path.join(
                os.path.dirname(__file__), "responses", "github_label_payload.json"
            ),
            "r",
        ) as f:
            mock_request = amock.CoroutineMock()
            mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
            self.connector.opsdroid = amock.CoroutineMock()
            self.connector.opsdroid.parse = amock.CoroutineMock()
            await self.connector.github_message_handler(mock_request)
            self.assertFalse(self.connector.opsdroid.parse.called)

    async def test_get_no_action(self):
        """Test a status event doesn't create a message and parse it."""
        with open(
            os.path.join(
                os.path.dirname(__file__), "responses", "github_status_payload.json"
            ),
            "r",
        ) as f:
            mock_request = amock.CoroutineMock()
            mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
            self.connector.opsdroid = amock.CoroutineMock()
            self.connector.opsdroid.parse = amock.CoroutineMock()
            await self.connector.github_message_handler(mock_request)
            self.assertFalse(self.connector.opsdroid.parse.called)

    async def test_listen(self):
        """Test the listen method.

        The GitHub connector listens using an API endoint and so the listen
        method should just pass and do nothing. We just need to test that it
        does not block.

        """
        self.assertEqual(await self.connector.listen(), None)

    async def test_respond(self):
        with amock.patch("aiohttp.ClientSession.post") as patched_request:
            mockresponse = amock.CoroutineMock()
            mockresponse.status = 201
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(mockresponse)
            resp = await self.connector.send(
                Message("test", "jacobtomlinson", "opsdroid/opsdroid#1", self.connector)
            )
            self.assertTrue(patched_request.called)
            self.assertTrue(resp)

    async def test_respond_bot_short(self):
        with amock.patch("aiohttp.ClientSession.post") as patched_request:
            mockresponse = amock.CoroutineMock()
            mockresponse.status = 201
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(mockresponse)
            self.connector.github_username = "opsdroid-bot"
            resp = await self.connector.send(
                Message("test", "opsdroid-bot", "opsdroid/opsdroid#1", self.connector)
            )
            self.assertFalse(patched_request.called)
            self.assertTrue(resp)

    async def test_respond_failure(self):
        with amock.patch("aiohttp.ClientSession.post") as patched_request:
            mockresponse = amock.CoroutineMock()
            mockresponse.status = 400
            mockresponse.json = amock.CoroutineMock(
                return_value={"error": "some error"}
            )
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(mockresponse)
            resp = await self.connector.send(
                Message("test", "opsdroid-bot", "opsdroid/opsdroid#1", self.connector)
            )
            self.assertTrue(patched_request.called)
            self.assertFalse(resp)

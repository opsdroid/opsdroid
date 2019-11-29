"""Tests for the ConnectorSlack class."""
import asyncio

import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock
import slack
import json

from opsdroid.core import OpsDroid
from opsdroid.connector.slack import ConnectorSlack
from opsdroid.connector.slack.events import Blocks
from opsdroid.events import Message, Reaction
from opsdroid.cli.start import configure_lang


class TestConnectorSlack(unittest.TestCase):
    """Test the opsdroid Slack connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        configure_lang({})

    def test_init(self):
        """Test that the connector is initialised properly."""
        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        self.assertEqual("#general", connector.default_target)
        self.assertEqual("slack", connector.name)
        self.assertEqual(10, connector.timeout)

    def test_missing_api_key(self):
        """Test that creating without an API key raises an error."""
        with self.assertRaises(KeyError):
            ConnectorSlack({}, opsdroid=OpsDroid())

    # def test_listen(self):
    #     connector = ConnectorSlack({})
    #     with self.assertRaises(NotImplementedError):
    #         self.loop.run_until_complete(connector.listen({}))

    # def test_respond(self):
    #     connector = ConnectorSlack({})
    #     with self.assertRaises(NotImplementedError):
    #         self.loop.run_until_complete(connector.send({}))

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

    async def setUp(self):
        configure_lang({})

    async def test_connect(self):
        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        opsdroid = amock.CoroutineMock()
        opsdroid.eventloop = self.loop
        connector.slack_rtm._connect_and_read = amock.CoroutineMock()
        connector.slack.api_call = amock.CoroutineMock()
        connector.opsdroid.web_server = amock.CoroutineMock()
        connector.opsdroid.web_server.web_app = amock.CoroutineMock()
        connector.opsdroid.web_server.web_app.router = amock.CoroutineMock()
        connector.opsdroid.web_server.web_app.router.add_post = amock.CoroutineMock()
        await connector.connect()
        self.assertTrue(connector.slack_rtm._connect_and_read.called)
        self.assertTrue(connector.slack.api_call.called)
        self.assertTrue(connector.opsdroid.web_server.web_app.router.add_post.called)

    async def test_connect_auth_fail(self):
        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        opsdroid = amock.CoroutineMock()
        opsdroid.eventloop = self.loop
        connector.slack_rtm._connect_and_read = amock.Mock()
        connector.slack_rtm._connect_and_read.side_effect = slack.errors.SlackApiError(
            message="", response=""
        )

        await connector.connect()
        self.assertLogs("_LOGGER", "error")

    async def test_abort_on_connection_error(self):
        connector = ConnectorSlack({"token": "abc123"})
        connector.slack_rtm._connect_and_read = amock.CoroutineMock()
        connector.slack_rtm._connect_and_read.side_effect = Exception()
        connector.slack_rtm.stop = amock.CoroutineMock()

        with self.assertRaises(Exception):
            await connector.connect()
        self.assertTrue(connector.slack_rtm.stop.called)

    async def test_listen_loop(self):
        """Test that listening consumes from the socket."""
        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        connector.listening = False
        await connector.listen()

    async def test_process_message(self):
        """Test processing a slack message."""
        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        connector.lookup_username = amock.CoroutineMock()
        connector.lookup_username.return_value = {"name": "testuser"}
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()

        message = {  # https://api.slack.com/events/message
            "type": "message",
            "channel": "C2147483705",
            "user": "U2147483697",
            "text": "Hello, world!",
            "ts": "1355517523.000005",
            "edited": {"user": "U2147483697", "ts": "1355517536.000001"},
        }
        await connector.process_message(data=message)
        self.assertTrue(connector.opsdroid.parse.called)

        connector.opsdroid.parse.reset_mock()
        message["bot_id"] = "abc"
        message["subtype"] = "bot_message"
        connector.bot_id = message["bot_id"]
        await connector.process_message(data=message)
        self.assertFalse(connector.opsdroid.parse.called)
        del message["bot_id"]
        del message["subtype"]
        connector.bot_id = None

        connector.opsdroid.parse.reset_mock()
        message["subtype"] = "message_changed"
        await connector.process_message(data=message)
        self.assertFalse(connector.opsdroid.parse.called)
        del message["subtype"]

        connector.opsdroid.parse.reset_mock()
        connector.lookup_username.side_effect = ValueError
        await connector.process_message(data=message)
        self.assertFalse(connector.opsdroid.parse.called)

    async def test_lookup_username(self):
        """Test that looking up a username works and that it caches."""
        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        connector.slack.users_info = amock.CoroutineMock()
        mock_user = mock.Mock()
        mock_user.data = {"user": {"name": "testuser"}}
        connector.slack.users_info.return_value = mock_user

        self.assertEqual(len(connector.known_users), 0)

        await connector.lookup_username("testuser")
        self.assertTrue(len(connector.known_users), 1)
        self.assertTrue(connector.slack.users_info.called)

        connector.slack.users_info.reset_mock()
        await connector.lookup_username("testuser")
        self.assertEqual(len(connector.known_users), 1)
        self.assertFalse(connector.slack.users_info.called)

        with self.assertRaises(ValueError):
            mock_user.data = {"user": None}
            connector.slack.users_info.return_value = mock_user
            await connector.lookup_username("invaliduser")

    async def test_respond(self):
        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        connector.slack.api_call = amock.CoroutineMock()
        await connector.send(
            Message(text="test", user="user", target="room", connector=connector)
        )
        self.assertTrue(connector.slack.api_call.called)

    async def test_send_blocks(self):
        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        connector.slack.api_call = amock.CoroutineMock()
        await connector.send(
            Blocks(
                [{"type": "section", "text": {"type": "mrkdwn", "text": "*Test*"}}],
                "user",
                "room",
                connector,
            )
        )
        self.assertTrue(connector.slack.api_call.called)

    async def test_react(self):
        connector = ConnectorSlack({"token": "abc123"})
        connector.slack.api_call = amock.CoroutineMock()
        prev_message = Message(
            text="test",
            user="user",
            target="room",
            connector=connector,
            raw_event={"ts": 0},
        )
        with OpsDroid():
            await prev_message.respond(Reaction("😀"))
        self.assertTrue(connector.slack.api_call)
        self.assertEqual(
            connector.slack.api_call.call_args[1]["data"]["name"], "grinning_face"
        )

    async def test_react_invalid_name(self):
        import slack

        connector = ConnectorSlack({"token": "abc123"})
        connector.slack.api_call = amock.CoroutineMock(
            side_effect=slack.errors.SlackApiError("invalid_name", "invalid_name")
        )
        prev_message = Message(
            text="test",
            user="user",
            target="room",
            connector=connector,
            raw_event={"ts": 0},
        )
        with OpsDroid():
            await prev_message.respond(Reaction("😀"))
        self.assertLogs("_LOGGER", "warning")

    async def test_react_unknown_error(self):
        import slack

        connector = ConnectorSlack({"token": "abc123"})
        connector.slack.api_call = amock.CoroutineMock(
            side_effect=slack.errors.SlackApiError("unknown", "unknown")
        )
        with self.assertRaises(slack.errors.SlackApiError), OpsDroid():
            prev_message = Message(
                text="test",
                user="user",
                target="room",
                connector=connector,
                raw_event={"ts": 0},
            )
            await prev_message.respond(Reaction("😀"))

    async def test_replace_usernames(self):
        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        connector.lookup_username = amock.CoroutineMock()
        connector.lookup_username.return_value = {"name": "user"}
        result = await connector.replace_usernames("Hello <@U023BECGF>!")
        self.assertEqual(result, "Hello user!")

    async def test_block_actions_interactivity(self):
        """Test the block_actions interactivity type in Slack interactions handler."""

        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()

        req_ob = {
            "type": "block_actions",
            "team": {"id": "T9TK3CUKW", "domain": "example"},
            "user": {
                "id": "UA8RXUSPL",
                "username": "jtorrance",
                "team_id": "T9TK3CUKW",
            },
            "channel": {"id": "CBR2V3XEX", "name": "review-updates"},
            "actions": [
                {
                    "action_id": "WaXA",
                    "block_id": "=qXel",
                    "text": {"type": "plain_text", "text": "View", "emoji": True},
                    "value": "click_me_123",
                    "type": "button",
                    "action_ts": "1548426417.840180",
                }
            ],
        }

        mock_request = amock.CoroutineMock()
        mock_request.post = amock.CoroutineMock()
        mock_request.post.return_value = {"payload": json.dumps(req_ob)}

        response = await connector.slack_interactions_handler(mock_request)
        self.assertTrue(connector.opsdroid.parse.called)
        self.assertEqual(type(response), aiohttp.web.Response)
        self.assertEqual(response.status, 200)

    async def test_message_action_interactivity(self):
        """Test the message_action interactivity type in Slack interactions handler."""

        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()

        req_ob = {
            "token": "Nj2rfC2hU8mAfgaJLemZgO7H",
            "callback_id": "chirp_message",
            "type": "message_action",
            "trigger_id": "13345224609.8534564800.6f8ab1f53e13d0cd15f96106292d5536",
            "response_url": "https://hooks.slack.com/app-actions/T0MJR11A4/21974584944/yk1S9ndf35Q1flupVG5JbpM6",
            "team": {"id": "T0MJRM1A7", "domain": "pandamonium"},
            "channel": {"id": "D0LFFBKLZ", "name": "cats"},
            "user": {"id": "U0D15K92L", "name": "dr_maomao"},
            "message": {
                "type": "message",
                "user": "U0MJRG1AL",
                "ts": "1516229207.000133",
                "text": "World's smallest big cat! <https://youtube.com/watch?v=W86cTIoMv2U>",
            },
        }

        mock_request = amock.CoroutineMock()
        mock_request.post = amock.CoroutineMock()
        mock_request.post.return_value = {"payload": json.dumps(req_ob)}

        response = await connector.slack_interactions_handler(mock_request)
        self.assertTrue(connector.opsdroid.parse.called)
        self.assertEqual(type(response), aiohttp.web.Response)
        self.assertEqual(response.status, 200)

    async def test_view_submission_interactivity(self):
        """Test the view_submission interactivity type in Slack interactions handler."""

        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()

        req_ob = {
            "type": "view_submission",
            "team": {"id": "T0MJRM1A7", "domain": "pandamonium"},
            "user": {"id": "U0D15K92L", "name": "dr_maomao"},
            "view": {
                "id": "VNHU13V36",
                "type": "modal",
                "private_metadata": "shhh-its-secret",
                "callback_id": "modal-with-inputs",
                "state": {
                    "values": {
                        "multi-line": {
                            "ml-value": {
                                "type": "plain_text_input",
                                "value": "This is my example inputted value",
                            }
                        }
                    }
                },
                "hash": "156663117.cd33ad1f",
            },
        }

        mock_request = amock.CoroutineMock()
        mock_request.post = amock.CoroutineMock()
        mock_request.post.return_value = {"payload": json.dumps(req_ob)}

        response = await connector.slack_interactions_handler(mock_request)
        self.assertTrue(connector.opsdroid.parse.called)
        self.assertEqual(type(response), aiohttp.web.Response)
        self.assertEqual(response.status, 200)

    async def test_view_closed_interactivity(self):
        """Test the view_closed interactivity type in Slack interactions handler."""

        connector = ConnectorSlack({"token": "abc123"}, opsdroid=OpsDroid())
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()

        req_ob = {
            "type": "view_closed",
            "team": {"id": "TXXXXXX", "domain": "coverbands"},
            "user": {"id": "UXXXXXX", "name": "dreamweaver"},
            "view": {
                "id": "VNHU13V36",
                "type": "modal",
                "private_metadata": "shhh-its-secret",
                "callback_id": "modal-with-inputs",
                "state": {
                    "values": {
                        "multi-line": {
                            "ml-value": {
                                "type": "plain_text_input",
                                "value": "This is my example inputted value",
                            }
                        }
                    }
                },
                "hash": "156663117.cd33ad1f",
            },
            "api_app_id": "AXXXXXX",
            "is_cleared": false,
        }

        mock_request = amock.CoroutineMock()
        mock_request.post = amock.CoroutineMock()
        mock_request.post.return_value = {"payload": json.dumps(req_ob)}

        response = await connector.slack_interactions_handler(mock_request)
        self.assertTrue(connector.opsdroid.parse.called)
        self.assertEqual(type(response), aiohttp.web.Response)
        self.assertEqual(response.status, 200)

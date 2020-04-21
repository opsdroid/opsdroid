import asyncio
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock
import slack
import json
import collections

import aiohttp

from opsdroid.core import OpsDroid
from opsdroid.connector.slack import ConnectorSlack
from opsdroid.connector.slack import events as slackevents
from opsdroid import events
from opsdroid.cli.start import configure_lang


class TestEventCreatorAsync(asynctest.TestCase):
    def setUp(self):
        self.od = OpsDroid()
        self.od.__enter__()
        self.connector = ConnectorSlack({"token": "abc123"}, opsdroid=self.od)
        self.event_creator = slackevents.SlackEventCreator(
            self.connector, self.connector.slack_rtm
        )

    def tearDown(self):
        slack.RTMClient._callbacks = collections.defaultdict(list)
        del self.connector
        del self.event_creator
        self.od.__exit__(None, None, None)
        del self.od

    @property
    def message_event(self):
        return {
            "text": "Hello World",
            "user": "U9S8JGF45",
            "team": "T9T6EKEEB",
            "source_team": "T9T6EKEEB",
            "user_team": "T9T6EKEEB",
            "channel": "C9S8JGM2R",
            "event_ts": "1582838099.000600",
            "ts": "1582838099.000600",
        }

    async def test_create_message(self):
        with amock.patch(
            "opsdroid.connector.slack.ConnectorSlack.lookup_username"
        ) as lookup, amock.patch("opsdroid.core.OpsDroid.parse") as parse:
            lookup.return_value = asyncio.Future()
            lookup.return_value.set_result({"name": "testuser"})

            await self.connector.slack_rtm._dispatch_event(
                "message", self.message_event
            )
            (called_event,), _ = parse.call_args
            self.assertTrue(isinstance(called_event, events.Message))
            self.assertTrue(called_event.text == self.message_event["text"])
            self.assertTrue(called_event.user == "testuser")
            self.assertTrue(called_event.user_id == self.message_event["user"])
            self.assertTrue(called_event.target == self.message_event["channel"])
            self.assertTrue(called_event.event_id == self.message_event["ts"])
            self.assertTrue(called_event.raw_event == self.message_event)
            lookup.assert_called_once_with("U9S8JGF45")

    async def test_create_message_no_user(self):
        with amock.patch(
            "opsdroid.connector.slack.events.SlackEventCreator._get_user_name"
        ) as getuser, amock.patch("opsdroid.core.OpsDroid.parse") as parse:
            getuser.return_value = asyncio.Future()
            getuser.return_value.set_result(None)

            await self.connector.slack_rtm._dispatch_event(
                "message", self.message_event
            )

            parse.assert_not_called()

    @property
    def bot_message_event(self):
        return {
            "subtype": "bot_message",
            "text": "Hello",
            "username": "Robot",
            "bot_id": "BDATLJZKQ",
            "team": "T9T6EKEEB",
            "bot_profile": {
                "id": "BDATLJZKQ",
                "deleted": False,
                "name": "rss",
                "updated": 1539016312,
                "app_id": "A0F81R7U7",
                "team_id": "T9T6EKEEB",
            },
            "channel": "C9S8JGM2R",
            "event_ts": "1582841283.001700",
            "ts": "1582841283.001700",
        }

    async def test_create_message_from_bot(self):
        # Skip this test until we have implemented bot user name lookup
        return
        with amock.patch("opsdroid.core.OpsDroid.parse") as parse:

            await self.connector.slack_rtm._dispatch_event(
                "message", self.bot_message_event
            )
            (called_event,), _ = parse.call_args
            self.assertTrue(isinstance(called_event, events.Message))
            self.assertTrue(called_event.text == self.bot_message_event["text"])
            self.assertTrue(called_event.user == "testuser")
            self.assertTrue(called_event.user_id == self.bot_message_event["user"])
            self.assertTrue(called_event.target == self.bot_message_event["channel"])
            self.assertTrue(called_event.event_id == self.bot_message_event["ts"])
            self.assertTrue(called_event.raw_event == self.bot_message_event)

    async def test_ignore_own_bot_message(self):
        self.connector.bot_id = self.bot_message_event["bot_id"]
        with amock.patch("opsdroid.core.OpsDroid.parse") as parse:

            await self.connector.slack_rtm._dispatch_event(
                "message", self.bot_message_event
            )
            self.assertFalse(parse.called)
            self.connector.bot_id = None

    @property
    def channel_created_event(self):
        return {
            "channel": {
                "id": "CUM24109W",
                "is_channel": True,
                "name": "test100",
                "name_normalized": "test100",
                "created": 1582843467,
                "creator": "U9S8JGF45",
                "is_shared": False,
                "is_org_shared": False,
            },
            "event_ts": "1582843467.006500",
        }

    async def test_create_channel_created_event(self):
        with amock.patch(
            "opsdroid.connector.slack.ConnectorSlack.lookup_username"
        ) as lookup, amock.patch("opsdroid.core.OpsDroid.parse") as parse:
            lookup.return_value = asyncio.Future()
            lookup.return_value.set_result({"name": "testuser"})

            await self.connector.slack_rtm._dispatch_event(
                "channel_created", self.channel_created_event
            )
            (called_event,), _ = parse.call_args
            self.assertTrue(isinstance(called_event, events.NewRoom))
            self.assertTrue(
                called_event.user_id == self.channel_created_event["channel"]["creator"]
            )
            self.assertTrue(called_event.user == "testuser")
            self.assertTrue(
                called_event.target == self.channel_created_event["channel"]["id"]
            )
            self.assertTrue(called_event.connector == self.connector)
            self.assertTrue(
                called_event.event_id == self.channel_created_event["event_ts"]
            )
            self.assertTrue(
                called_event.name == self.channel_created_event["channel"]["name"]
            )
            lookup.assert_called_once_with("U9S8JGF45")

    @property
    def channel_archive_event(self):
        return {
            "channel": "CULJAHTUL",
            "user": "U9S8JGF45",
            "is_moved": 0,
            "event_ts": "1582843733.007500",
        }

    async def test_create_channel_archive_event(self):
        with amock.patch(
            "opsdroid.connector.slack.ConnectorSlack.lookup_username"
        ) as lookup, amock.patch("opsdroid.core.OpsDroid.parse") as parse:
            lookup.return_value = asyncio.Future()
            lookup.return_value.set_result({"name": "testuser"})

            await self.connector.slack_rtm._dispatch_event(
                "channel_archive", self.channel_archive_event
            )
            (called_event,), _ = parse.call_args
            self.assertTrue(isinstance(called_event, slackevents.ChannelArchived))
            self.assertTrue(
                called_event.target == self.channel_archive_event["channel"]
            )
            self.assertTrue(called_event.connector == self.connector)
            self.assertTrue(
                called_event.event_id == self.channel_archive_event["event_ts"]
            )

    @property
    def channel_unarchive_event(self):
        return {
            "channel": "CULJAHTUL",
            "user": "U9S8JGF45",
            "event_ts": "1582843808.007700",
        }

    async def test_create_channel_unarchive_event(self):
        with amock.patch(
            "opsdroid.connector.slack.ConnectorSlack.lookup_username"
        ) as lookup, amock.patch("opsdroid.core.OpsDroid.parse") as parse:
            lookup.return_value = asyncio.Future()
            lookup.return_value.set_result({"name": "testuser"})

            await self.connector.slack_rtm._dispatch_event(
                "channel_unarchive", self.channel_unarchive_event
            )
            (called_event,), _ = parse.call_args
            self.assertTrue(isinstance(called_event, slackevents.ChannelUnarchived))
            self.assertTrue(
                called_event.target == self.channel_unarchive_event["channel"]
            )
            self.assertTrue(called_event.connector == self.connector)
            self.assertTrue(
                called_event.event_id == self.channel_unarchive_event["event_ts"]
            )

    @property
    def join_event(self):
        return {
            "user": {
                "id": "UV6E5JA5T",
                "team_id": "T9T6EKEEB",
                "name": "slack1",
                "deleted": False,
                "color": "99a949",
                "real_name": "test4",
                "tz": "Europe/London",
                "tz_label": "Greenwich Mean Time",
                "tz_offset": 0,
                "profile": {
                    "title": "",
                    "phone": "",
                    "skype": "",
                    "real_name": "test4",
                    "real_name_normalized": "test4",
                    "display_name": "test4",
                    "display_name_normalized": "test4",
                    "fields": None,
                    "status_text": "",
                    "status_emoji": "",
                    "status_expiration": 0,
                    "avatar_hash": "gaa2e6c047a5",
                    "status_text_canonical": "",
                    "team": "T9T6EKEEB",
                },
                "is_admin": False,
                "is_owner": False,
                "is_primary_owner": False,
                "is_restricted": False,
                "is_ultra_restricted": False,
                "is_bot": False,
                "is_app_user": False,
                "updated": 1583879206,
                "presence": "away",
            },
            "cache_ts": 1583879206,
            "event_ts": "1583879207.001200",
        }

    async def test_user_join(self):
        with amock.patch(
            "opsdroid.connector.slack.ConnectorSlack.lookup_username"
        ) as lookup, amock.patch("opsdroid.core.OpsDroid.parse") as parse:
            lookup.return_value = asyncio.Future()
            lookup.return_value.set_result({"name": "testuser"})

            await self.connector.slack_rtm._dispatch_event("team_join", self.join_event)
            lookup.assert_called_with("UV6E5JA5T")
            (called_event,), _ = parse.call_args
            assert isinstance(called_event, events.JoinGroup)
            self.assertTrue(called_event.user == "testuser")
            self.assertTrue(called_event.user_id == self.join_event["user"]["id"])
            self.assertTrue(called_event.target == self.join_event["user"]["team_id"])
            self.assertTrue(called_event.event_id == self.join_event["event_ts"])
            self.assertTrue(called_event.raw_event == self.join_event)

    @property
    def edit_event(self):
        return {
            "subtype": "message_changed",
            "hidden": True,
            "message": {
                "type": "message",
                "text": "Hello World",
                "user": "U9S8JGF45",
                "team": "T9T6EKEEB",
                "edited": {"user": "U9S8JGF45", "ts": "1582842709.000000"},
                "ts": "1582842695.003200",
                "source_team": "T9T6EKEEB",
                "user_team": "T9T6EKEEB",
            },
            "channel": "C9S8JGM2R",
            "previous_message": {
                "type": "message",
                "text": "Hi",
                "user": "U9S8JGF45",
                "ts": "1582842695.003200",
                "team": "T9T6EKEEB",
            },
            "event_ts": "1582842709.003300",
            "ts": "1582842709.003300",
        }

    async def test_create_message_from_edit(self):
        with amock.patch(
            "opsdroid.connector.slack.ConnectorSlack.lookup_username"
        ) as lookup, amock.patch("opsdroid.core.OpsDroid.parse") as parse:
            lookup.return_value = asyncio.Future()
            lookup.return_value.set_result({"name": "testuser"})

            await self.connector.slack_rtm._dispatch_event("message", self.edit_event)
            assert parse.called is False
            # lookup.assert_called_once_with("U9S8JGF45")

    async def test_create_event_fails(self):
        # The create_event method of the event creator is redundant in slack because the RTM is
        # doing the heavy lifting on that. Check that it fails loudly if it gets called.
        with self.assertRaises(NotImplementedError):
            await self.event_creator.create_event(self.message_event, "hello")

    async def test_get_user_name(self):
        # Check that username lookup works with a username
        with amock.patch(
            "opsdroid.connector.slack.ConnectorSlack.lookup_username"
        ) as lookup:
            lookup.return_value = asyncio.Future()
            lookup.return_value.set_result({"name": "testuser"})
            username = await self.event_creator._get_user_name(self.message_event)
            assert username == "testuser"

    async def test_get_user_name_fails(self):
        # Check that username lookup works without a username
        userless_event = self.message_event
        del userless_event["user"]
        user_info = await self.event_creator._get_user_name(userless_event)
        assert user_info is None

    @property
    def channel_name_event(self):
        return {
            "type": "channel_rename",
            "channel": {"id": "C02ELGNBH", "name": "new_name", "created": 1360782804},
            "event_ts": "1582842709.003300",
            "ts": "1582842709.003300",
        }

    async def test_channel_rename(self):
        with amock.patch(
            "opsdroid.connector.slack.ConnectorSlack.lookup_username"
        ) as lookup, amock.patch("opsdroid.core.OpsDroid.parse") as parse:
            await self.connector.slack_rtm._dispatch_event(
                "channel_rename", self.channel_name_event
            )
            (called_event,), _ = parse.call_args
            assert isinstance(called_event, events.RoomName)
            assert called_event.name == self.channel_name_event["channel"]["name"]
            assert called_event.target == self.channel_name_event["channel"]["id"]
            assert called_event.connector == self.connector
            assert called_event.event_id == self.channel_name_event["event_ts"]
            lookup.assert_not_called()

    @property
    def pin_added_event(self):
        return {
            "type": "pin_added",
            "user": "U024BE7LH",
            "channel_id": "C02ELGNBH",
            "item": self.message_event,
            "event_ts": "1582842709.003301",
        }

    async def test_pin_message(self):
        with amock.patch(
            "opsdroid.connector.slack.ConnectorSlack.lookup_username"
        ) as lookup, amock.patch("opsdroid.core.OpsDroid.parse") as parse:
            await self.connector.slack_rtm._dispatch_event(
                "pin_added", self.pin_added_event
            )
            (called_event,), _ = parse.call_args
            assert isinstance(called_event, events.PinMessage)
            assert called_event.target == self.pin_added_event["channel_id"]
            assert called_event.connector == self.connector
            assert called_event.event_id == self.pin_added_event["event_ts"]
            assert called_event.linked_event == self.message_event
            lookup.assert_not_called()

    @property
    def pin_removed_event(self):
        return {
            "type": "pin_removed",
            "user": "U024BE7LH",
            "channel_id": "C02ELGNBH",
            "item": self.message_event,
            "event_ts": "1582842709.003302",
        }

    async def test_unpin_message(self):
        with amock.patch(
            "opsdroid.connector.slack.ConnectorSlack.lookup_username"
        ) as lookup, amock.patch("opsdroid.core.OpsDroid.parse") as parse:
            await self.connector.slack_rtm._dispatch_event(
                "pin_removed", self.pin_removed_event
            )
            (called_event,), _ = parse.call_args
            assert isinstance(called_event, events.UnpinMessage)
            assert called_event.target == self.pin_removed_event["channel_id"]
            assert called_event.connector == self.connector
            assert called_event.event_id == self.pin_removed_event["event_ts"]
            assert called_event.linked_event == self.message_event
            lookup.assert_not_called()

    @property
    def topic_changed_event(self):
        return {
            "subtype": "channel_topic",
            "user": "U9S8JGF45",
            "text": "<@U9S8JGF45> set the channel topic: New topic",
            "topic": "New topic",
            "team": "T9T6EKEEB",
            "channel": "CUTKP9FDG",
            "event_ts": "1587296471.000100",
            "ts": "1587296471.000100",
        }

    async def test_topic_change(self):
        with amock.patch(
            "opsdroid.connector.slack.ConnectorSlack.lookup_username"
        ) as lookup, amock.patch("opsdroid.core.OpsDroid.parse") as parse:
            await self.connector.slack_rtm._dispatch_event(
                "message", self.topic_changed_event
            )
            (called_event,), _ = parse.call_args
            assert isinstance(called_event, events.RoomDescription)
            assert called_event.target == self.topic_changed_event["channel"]
            assert called_event.connector == self.connector
            assert called_event.event_id == self.topic_changed_event["event_ts"]
            assert called_event.description == self.topic_changed_event["topic"]
            lookup.assert_not_called()

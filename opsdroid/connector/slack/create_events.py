"""A helper module to create opsdroid events from Slack events."""
import logging
from collections import defaultdict

from opsdroid import events
from opsdroid.connector.slack import events as slack_events

_LOGGER = logging.getLogger(__name__)


class SlackEventCreator(events.EventCreator):
    """Create opsdroid events from Slack ones."""

    def __init__(self, connector, *args, **kwargs):
        """Initialise the event creator."""
        super().__init__(connector, *args, **kwargs)
        self.connector = connector
        self.event_types["message"] = self.create_room_message
        self.event_types["channel_created"] = self.create_newroom
        self.event_types["channel_archive"] = self.archive_room
        self.event_types["channel_unarchive"] = self.unarchive_room
        self.event_types["team_join"] = self.create_join_group
        self.event_types["channel_rename"] = self.channel_name_changed
        self.event_types["pin_added"] = self.message_pinned
        self.event_types["pin_removed"] = self.message_unpinned
        self.event_types["block_actions"] = self.block_actions_triggered
        self.event_types["message_action"] = self.message_action_triggered
        self.event_types["view_submission"] = self.view_submission_triggered
        self.event_types["view_closed"] = self.view_closed_triggered
        self.event_types["command"] = self.slash_command

        self.message_subtypes = defaultdict(lambda: self.create_message)
        self.message_subtypes.update(
            {
                "message": self.create_message,
                "bot_message": self.handle_bot_message,
                "message_changed": self.edit_message,
                "channel_join": self.handle_channel_join,
            }
        )

    async def create_room_message(self, event, channel):
        """Dispatch a message event of arbitrary subtype."""
        channel = event["channel"]
        msgtype = event["subtype"] if "subtype" in event.keys() else "message"

        return await self.message_subtypes[msgtype](event, channel)

    async def _get_user_name(self, event):
        try:
            user_info = await self.connector.lookup_username(event["user"])
        except (ValueError, KeyError) as error:
            _LOGGER.error(_("Username lookup failed for %s."), error)

            return

        return user_info["name"]

    async def handle_bot_message(self, event, channel):
        """Check that a bot message is opsdroid if not create the message"""

        if event["bot_id"] != self.connector.bot_id:
            return await self.create_message(event, channel)

    async def create_message(self, event, channel):
        """Send a Message event."""

        user_name = await self._get_user_name(event)

        if user_name is None:
            return

        _LOGGER.debug("Replacing userids in message with usernames")
        text = await self.connector.replace_usernames(event["text"])

        return events.Message(
            text,
            user=user_name,
            user_id=event["user"],
            target=event["channel"],
            connector=self.connector,
            event_id=event["ts"],
            raw_event=event,
        )

    async def edit_message(self, event, channel):
        """Send an EditedMessage event."""
        user_name = await self._get_user_name(event["message"])

        if user_name is None:
            return

        _LOGGER.debug("Replacing userids in message with usernames")
        text = await self.connector.replace_usernames(event["message"]["text"])

        return events.EditedMessage(
            text,
            user=user_name,
            user_id=event["message"]["user"],
            target=event["channel"],
            connector=self.connector,
            event_id=event["ts"],
            linked_event=event["message"]["ts"],
            raw_event=event,
        )

    async def handle_channel_join(self, event, channel):
        """Send a JoinRoom event when a user joins the channel."""
        user_id = event["user"]
        user_info = await self.connector.lookup_username(user_id)

        return events.JoinRoom(
            user_id=user_id,
            user=user_info["name"],
            target=event["channel"],
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    async def create_newroom(self, event, channel):
        """Send a NewRoom event."""
        user_id = event["channel"]["creator"]
        user_info = await self.connector.lookup_username(user_id)

        name = event["channel"].get("name_normalized", event["channel"].get("name"))

        return events.NewRoom(
            name=name,
            params=None,
            user=user_info["name"],
            user_id=user_id,
            target=event["channel"]["id"],
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    async def archive_room(self, event, channel):
        """Send a ChannelArchived event."""

        return slack_events.ChannelArchived(
            target=event["channel"],
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    async def unarchive_room(self, event, channel):
        """Send a ChannelUnarchived event."""

        return slack_events.ChannelUnarchived(
            target=event["channel"],
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    async def create_join_group(self, event, channel):
        """Send a JoinGroup event."""
        user_info = await self.connector.lookup_username(event["user"]["id"])

        return events.JoinGroup(
            target=event["user"]["team_id"],
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
            user_id=event["user"]["id"],
            user=user_info["name"],
        )

    async def channel_name_changed(self, event, channel):
        """Send a RoomName event."""

        return events.RoomName(
            name=event["channel"]["name"],
            target=event["channel"]["id"],
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    async def message_pinned(self, event, channel):
        """Send a PinMessage event."""

        return events.PinMessage(
            linked_event=event["item"],
            target=event["channel_id"],
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    async def message_unpinned(self, event, channel):
        """Send an UnpinMessage event."""

        return events.UnpinMessage(
            linked_event=event["item"],
            target=event["channel_id"],
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    async def block_actions_triggered(self, event, channel):
        """Send a BlockActions event."""
        block_actions = []

        for action in event["actions"]:
            block_action = slack_events.BlockActions(
                event,
                user=event["user"]["id"],
                target=event["channel"]["id"],
                connector=self.connector,
            )
            action_value = None
            action_id = action.get("action_id", None)
            block_id = action.get("block_id", None)

            if action["type"] == "button":
                action_value = action["value"]
            elif action["type"] in ["overflow", "static_select"]:
                action_value = action["selected_option"]["value"]
            elif action["type"] == "datepicker":
                action_value = action["selected_date"]
            elif action["type"] == "multi_static_select":
                action_value = [v["value"] for v in action["selected_options"]]

            if action_value:
                block_action.update_entity("value", action_value)
            if action_id:
                block_action.update_entity("action_id", action_id)
            if block_id:
                block_action.update_entity("block_id", block_id)
            block_actions.append(block_action)

        return block_actions

    async def message_action_triggered(self, event, channel):
        """Send a MessageAction event."""

        return slack_events.MessageAction(
            event,
            user=event["user"]["id"],
            target=event["channel"]["id"],
            connector=self.connector,
        )

    async def view_submission_triggered(self, event, channel):
        """Send a ViewSubmission event."""

        view_submission = slack_events.ViewSubmission(
            event,
            user=event["user"]["id"],
            target=event["user"]["id"],
            connector=self.connector,
        )

        if callback_id := event.get("view", {}).get("callback_id"):
            view_submission.update_entity("callback_id", callback_id)

        return view_submission

    async def view_closed_triggered(self, event, channel):
        """Send a ViewClosed event."""

        return slack_events.ViewClosed(
            event,
            user=event["user"]["id"],
            target=event["user"]["id"],
            connector=self.connector,
        )

    async def slash_command(self, event, channel):
        """Send a Slash command event"""

        command = slack_events.SlashCommand(
            payload=event,
            user=event["user_id"],
            target=event["channel_id"],
            connector=self.connector,
        )
        command.update_entity("command", event["command"])
        return command

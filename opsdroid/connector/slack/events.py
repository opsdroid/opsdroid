"""Classes to describe different kinds of Slack specific event."""

import json
import aiohttp
import ssl
import certifi
import logging
from collections import defaultdict

from opsdroid import events

_LOGGER = logging.getLogger(__name__)


class Blocks(events.Message):
    """A blocks object.

    Slack uses blocks to add advenced interactivity and formatting to messages.
    https://api.slack.com/messaging/interactivity
    Blocks are provided in JSON format to Slack which renders them.

    Args:
        blocks (string or dict): String or dict of json for blocks
        room (string, optional): String name of the room or chat channel in
                                 which message was sent
        connector (Connector, optional): Connector object used to interact with
                                         given chat service
        raw_event (dict, optional): Raw message as provided by chat service.
                                    None by default

    Attributes:
        created: Local date and time that message object was created
        user: String name of user sending message
        room: String name of the room or chat channel in which message was sent
        connector: Connector object used to interact with given chat service
        blocks: Blocks JSON as string
        raw_event: Raw message provided by chat service
        raw_match: A match object for a search against which the message was
            matched. E.g. a regular expression or natural language intent
        responded_to: Boolean initialized as False. True if event has been
            responded to

    """

    def __init__(self, blocks, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__("", *args, **kwargs)

        self.blocks = blocks
        if isinstance(self.blocks, list):
            self.blocks = json.dumps(self.blocks)


class EditedBlocks(Blocks):
    """A  `Blocks` slack instance which has been edited.

    The ``linked_event`` property should hold Time Stamp (ts) of the Block
    to be edited
    """


class InteractiveAction(events.Event):
    """Super class to represent Slack interactive actions."""

    def __init__(self, payload, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(*args, **kwargs)
        self.payload = payload
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    async def respond(self, response_event):
        """Respond to this message using the response_url field in the payload."""

        if isinstance(response_event, str):
            if "response_url" in self.payload:
                async with aiohttp.ClientSession() as session:
                    headers = {"Content-Type": "application/json"}
                    response = await session.post(
                        self.payload["response_url"],
                        data=json.dumps(
                            {
                                "text": response_event,
                                "replace_original": False,
                                "delete_original": False,
                                "response_type": "in_channel",
                            }
                        ),
                        headers=headers,
                        ssl=self.ssl_context,
                    )
                    response_txt = await response.json()
            else:
                response_txt = {"error": "Response URL not available in payload."}
        else:
            response_txt = await super().respond(response_event)

        return response_txt


class BlockActions(InteractiveAction):
    """Event class to represent block_actions in Slack."""

    def __init__(self, payload, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(payload, *args, **kwargs)


class MessageAction(InteractiveAction):
    """Event class to represent message_action in Slack."""

    def __init__(self, payload, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(payload, *args, **kwargs)


class ViewSubmission(InteractiveAction):
    """Event class to represent view_submission in Slack."""

    def __init__(self, payload, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(payload, *args, **kwargs)


class ViewClosed(InteractiveAction):
    """Event class to represent view_closed in Slack."""

    def __init__(self, payload, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(payload, *args, **kwargs)


class ChannelArchived(events.Event):
    """Event for when a slack channel is archived."""


class ChannelUnarchived(events.Event):
    """Event for when a slack channel is unarchived."""


def slack_to_creator(f):
    """Wrap a callback so that RTMClient can work."""

    async def wrapper(self, **kwargs):
        event = kwargs["data"]
        _LOGGER.debug(f"Got slack event: {event}")
        channel = event.get("channel", None)
        event = await f(self, event, channel)
        if event is not None:
            return await self.connector.opsdroid.parse(event)

    return wrapper


class SlackEventCreator(events.EventCreator):
    """Create opsdroid events from Slack ones."""

    def __init__(self, connector, *args, **kwargs):
        """Initialise the event creator."""
        super().__init__(connector, *args, **kwargs)
        self.connector = connector

        # Things for managing various types of message
        self.connector.slack_rtm.on(event="message", callback=self.create_room_message)
        self.connector.slack_rtm.on(
            event="channel_created", callback=self.create_newroom
        )
        self.connector.slack_rtm.on(event="channel_archive", callback=self.archive_room)
        self.connector.slack_rtm.on(
            event="channel_unarchive", callback=self.unarchive_room
        )
        self.connector.slack_rtm.on(event="team_join", callback=self.create_join_group)
        self.connector.slack_rtm.on(
            event="channel_rename", callback=self.channel_name_changed
        )
        self.connector.slack_rtm.on(event="pin_added", callback=self.message_pinned)
        self.connector.slack_rtm.on(event="pin_removed", callback=self.message_unpinned)

        self.message_subtypes = defaultdict(lambda: self.create_message)
        self.message_subtypes.update(
            {
                "message": self.create_message,
                "bot_message": self.handle_bot_message,
                "message_changed": self.handle_edit,
                "channel_topic": self.topic_changed,
            }
        )

    async def create_event(self, event, target):
        """Not Implemented."""
        # We don't use this, as we use the RTM client instead.
        # It's implemented in the base class though, so do this to be safe.
        raise NotImplementedError(
            "This method is not used with slack. Use connector.slack_rtm._dispatch_event() instead"
        )

    @slack_to_creator
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

    async def create_message(self, event, channel, user_name=None):
        """Send a Message event."""

        if user_name is None:
            user_name = await self._get_user_name(event)

        if user_name is None:
            return

        _LOGGER.debug("Replacing userids in message with usernames")
        text = await self.connector.replace_usernames(event["text"])

        return events.Message(
            text,
            user=user_name,
            user_id=event["user"],
            target=channel,
            connector=self.connector,
            event_id=event["ts"],
            raw_event=event,
        )

    async def handle_bot_message(self, event, channel):
        """Check that a bot message isn't us then create the message."""
        # TODO: Add a bot_id lookup here to get the display name of the bot and
        # pass it through to create_message
        if event["bot_id"] != self.connector.bot_id:  # pragma: nocover
            return await self.create_message(event, channel)

    @slack_to_creator
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

    @slack_to_creator
    async def archive_room(self, event, channel):
        """Send a ChannelArchived event."""
        return ChannelArchived(
            target=channel,
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    @slack_to_creator
    async def unarchive_room(self, event, channel):
        """Send a ChannelUnarchived event."""
        return ChannelUnarchived(
            target=channel,
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    @slack_to_creator
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

    async def handle_edit(self, event, channel):
        """Not Implemented."""
        # TODO: Make this return an EditedMessage event
        return

    @slack_to_creator
    async def channel_name_changed(self, event, channel):
        """Send a RoomName event."""
        return events.RoomName(
            name=channel["name"],
            target=channel["id"],
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    @slack_to_creator
    async def message_pinned(self, event, channel):
        """Send a PinMessage event."""
        # Note that the pin_added event in slack doesn't have a "channel" keyword.
        return events.PinMessage(
            linked_event=event["item"],
            target=event["channel_id"],
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    @slack_to_creator
    async def message_unpinned(self, event, channel):
        """Send an UnpinMessage event."""
        # Note that the pin_removed event in slack doesn't have a "channel" keyword.
        return events.UnpinMessage(
            linked_event=event["item"],
            target=event["channel_id"],
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

    async def topic_changed(self, event, channel):
        """Send a RoomDescription event."""
        _LOGGER.debug(_("New description: %s"), event["topic"])
        _LOGGER.debug(_("Target channel: %s"), event["channel"])
        return events.RoomDescription(
            description=event["topic"],
            target=channel,
            connector=self.connector,
            event_id=event["event_ts"],
            raw_event=event,
        )

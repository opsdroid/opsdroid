"""Classes to describe different kinds of Slack specific event."""

import json
import aiohttp
import ssl
import certifi

from opsdroid.events import Message, Event


class Blocks(Message):
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


class InteractiveAction(Event):
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

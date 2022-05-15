"""Classes to describe different kinds of Slack specific event."""

import json
import logging
import ssl

import aiohttp
import certifi
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

                    if response.content_type == "application/json":
                        response_txt = await response.json()
                    elif response.content_type == "text/html":
                        response_txt = await response.text()
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


class Modal(events.Event):
    """Base Event class to represent a Modal in Slack.

    Modals are the Slack app equivalent of alert boxes, pop-ups, or dialog boxes.
    https://api.slack.com/surfaces/modals/using

    args:
        view: a view payload. this can be a dict or a json encoded string
    """

    def __init__(self, view, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.view = view

        if isinstance(self.view, dict):
            self.view = json.dumps(self.view)


class ModalOpen(Modal):
    """Event class to represent a new Modal in Slack.

    args:
        trigger_id: trigger to post to a user

    **Basic Usage in a Skill:**

    .. code-block:: python

        from opsdroid.skill import Skill
        from opsdroid.matchers import match_event

        class ModalSkill(Skill):
            @match_event(SlashCommand, command="/testcommand")
            async def open_modal(self, event):
                view = {
                    "type": "modal",
                    "title": {"type": "plain_text", "text": "Modal title"},
                    "blocks": [
                        {
                            "type": "input",
                            "label": {"type": "plain_text", "text": "Input label"},
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "input1",
                                "placeholder": {
                                    "type": "plain_text",
                                    "text": "Type in here",
                                },
                                "multiline": False,
                            },
                            "optional": False,
                        },
                    ],
                    "close": {"type": "plain_text", "text": "Cancel"},
                    "submit": {"type": "plain_text", "text": "Save"},
                    "private_metadata": "Shhhhhhhh",
                    "callback_id": "view_identifier_12",
                }
                await self.opsdroid.send(
                    ModalOpen(view=view, trigger_id=event.payload["trigger_id"])
                )
    """

    def __init__(self, trigger_id, view, *args, **kwargs):
        super().__init__(view, *args, **kwargs)
        self.trigger_id = trigger_id


class ModalUpdate(Modal):
    """Event class to represent a Modal Update in Slack

    args:
        external_id: A unique identifier of the view set by the developer
        _hash: A string that represents view state to protect against possible race conditions
    """

    def __init__(self, external_id, view, *args, hash_=None, **kwargs):
        self.external_id = external_id
        self.hash = hash_
        super().__init__(view, *args, **kwargs)


class ModalPush(ModalOpen):
    """Event class to represent a Modal Push in Slack."""


class ViewSubmission(InteractiveAction):
    """Event class to represent view_submission in Slack."""

    def __init__(self, payload, *args, **kwargs):
        """Create object with minimum properties."""
        super().__init__(payload, *args, **kwargs)


class ViewClosed(InteractiveAction):
    """Event class to represent view_closed in Slack."""


class SlashCommand(InteractiveAction):
    """
    Event class to represent a slash command.

    args:
        payload: Incomming payload from the Slack API

    **Basic Usage in a Skill:**

    .. code-block:: python

        from opsdroid.skill import Skill
        from opsdroid.matchers import match_event

        class CommandsSkill(Skill):
            @match_event(SlashCommand, command="/testcommand")
            async def slash_command(self, event):

                cmd = event.payload["command"]

                # event.payload["text"] holds the arguments from the command
                arguments = event.payload["text"]

                await message.respond(f"{cmd} {arguments}")
    """


class ChannelArchived(events.Event):
    """Event for when a slack channel is archived."""


class ChannelUnarchived(events.Event):
    """Event for when a slack channel is unarchived."""

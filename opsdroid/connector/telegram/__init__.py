"""A connector for Telegram."""
import logging
import aiohttp
import secrets
import json
import emoji
from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import (
    Message,
    Image,
    File,
    EditedMessage,
    Reply,
    JoinGroup,
    LeaveGroup,
    PinMessage,
)
from . import events as telegram_events


_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = {
    Required("token"): str,
    "whitelisted-users": list,
    "bot-name": str,
    "reply-unauthorized": bool,
}


class ConnectorTelegram(Connector):
    """A connector the the char service Telegram."""

    def __init__(self, config, opsdroid=None):
        """Create the connector.

        Args:
            config (dict): configuration settings from the
                file config.yaml.
            opsdroid (OpsDroid): An instance of opsdroid.core.

        """
        _LOGGER.debug(_("Loaded Telegram Connector"))
        super().__init__(config, opsdroid=opsdroid)
        self.name = "telegram"
        self.bot_name = config.get("bot-name", "opsdroid")
        self.opsdroid = opsdroid
        self.latest_update = None
        self.whitelisted_users = config.get("whitelisted-users", None)
        self.session = None
        self.webhook_secret = secrets.token_urlsafe(18)
        self.base_url = opsdroid.config["web"]["base-url"]
        self.webhook_endpoint = f"/connector/{self.name}/{self.webhook_secret}"
        self.token = config["token"]

    @staticmethod
    def get_user(response, bot_name):
        """Get user from response.

        The API response is different depending on how
        the bot is set up and where the message is coming
        from.

        Since Telegram sends different payloads, depending of
        where the message is being sent from, this method tries
        to handle all the cases.

        If the message came from a channel, we use either the ``author_signature``
        or the bot name for the user and use the ``message_id`` for the ``user_id``,
        this is because channel posts don't contain users.

        Similarly, if a message was posted on a channel, Telegram will forward it to
        a group - if it was created from the channel. So we handle the case where there
        is a ``forward_signature`` in the payload otherwise we use the bot name.

        Args:
            response (dict): Response returned by aiohttp.ClientSession.
            bot_name (str): Name of the bot used in opsdroid configuration.

        """
        user = None
        user_id = None

        channel_post = response.get("channel_post")
        message = response.get("message")

        if channel_post:
            user = channel_post.get("author_signature", bot_name)
            user_id = channel_post.get("message_id", 0)

        if message:
            from_user = message.get("from")
            forwarded = message.get("forward_from_chat")

            user_id = from_user.get("id")

            if from_user:
                # TODO: Try to refactor these ifs
                if "username" in from_user:
                    user = from_user.get("username")

                elif "first_name" in from_user:
                    user = from_user.get("first_name")

            if forwarded:
                user = message.get("forward_signature", bot_name)

        return user, user_id

    def handle_user_permission(self, response, user, user_id):
        """Handle user permissions.

        This will check if the user that tried to talk with
        the bot is allowed to do so. It will also work with
        userid to improve security.

        """
        if (
            not self.whitelisted_users
            or user in self.whitelisted_users
            or user_id in self.whitelisted_users
        ):
            return True

        return False

    def build_url(self, method):
        """Build the url to connect to the API.

        Args:
            method (string): API call end point.

        Return:
            String that represents the full API url.

        """
        return "https://api.telegram.org/bot{}/{}".format(self.token, method)

    async def delete_webhook(self):
        """Delete Telegram webhook.

        TODO: Update docstring
        The Telegram api will thrown an 409 error when an webhook is
        active and a call to getUpdates is made. This method will
        try to request the deletion of the webhook to make the getUpdate
        request possible.

        """
        _LOGGER.debug(_("Sending deleteWebhook request to Telegram..."))
        async with aiohttp.ClientSession() as session:
            resp = await session.get(self.build_url("deleteWebhook"))

            if resp.status == 200:
                _LOGGER.debug(_("Telegram webhook deleted successfully."))
            else:
                _LOGGER.debug(_("Unable to delete webhook."))

    async def connect(self):
        """Connect to Telegram.

        TODO: Tidy up this docstring

        This method is not an authorization call. It basically
        checks if the API token was provided and makes an API
        call to Telegram and evaluates the status of the call.

        """
        self.opsdroid.web_server.web_app.router.add_post(
            self.webhook_endpoint, self.telegram_webhook_handler
        )

        async with aiohttp.ClientSession() as session:
            payload = {
                "url": f"{self.base_url}{self.webhook_endpoint}",
                "allowed_updates": [
                    "messages",
                    "edited_message",
                    "channel_post",
                    "edited_channel_post",
                    "update_id",
                ],
            }

            response = await session.post(self.build_url("setWebhook"), params=payload)

            _LOGGER.info(response)
            if response.status > 200:
                _LOGGER.info(
                    _("Error when connection to Telegram Webhook: - %s - %s"),
                    response.status,
                    response.text,
                )

    async def telegram_webhook_handler(self, request):
        """Handle webhook request."""
        payload = await request.json()
        user, user_id = self.get_user(payload, self.bot_name)

        _LOGGER.info(payload)
        if payload.get("edited_message"):
            event = EditedMessage(
                text=payload["text"],
                target=payload["chat"]["id"],
                user=user,
                user_id=user_id,
                connector=self,
            )

        if payload.get("message"):
            event = await self.handle_messages(
                payload["message"], user, user_id, payload["update_id"]
            )

        if payload.get("channel_post"):
            event = await self.handle_messages(
                payload["channel_post"], user, user_id, payload["update_id"]
            )

        if self.handle_user_permission(payload, user, user_id):
            await self.opsdroid.parse(event)
        else:
            if self.config.get("reply-unauthorized"):
                await self.send_message(
                    Message(text="Sorry, you're not allowed to speak with this bot.")
                )

        return aiohttp.web.Response(text=json.dumps("Received"), status=200)

    async def handle_messages(self, message, user, user_id, update_id):
        """Handle text messages received from Telegram.

        Telegram sends three types of text messages:
            - ``message`` - which is a plain text message received by DM
            - ``edited_message`` - any message that was edited
            - ``channel_post`` - message sent inside a channel

        """
        if message.get("new_chat_member"):
            event = JoinGroup(
                user=user,
                user_id=user_id,
                event_id=update_id,
                target=message["chat"]["id"],
                connector=self,
                raw_event=message,
            )

        if message.get("left_chat_member"):
            event = LeaveGroup(
                user=user,
                user_id=user_id,
                event_id=update_id,
                target=message["chat"]["id"],
                connector=self,
                raw_event=message,
            )

        if message.get("pinned_message"):
            event = PinMessage(
                user=user,
                user_id=user_id,
                event_id=update_id,
                target=message["chat"]["id"],
                connector=self,
                raw_event=message,
            )

        if message.get("reply_to_message"):
            event = Reply(
                text=emoji.demojize(message["text"]),
                user=user,
                user_id=user_id,
                event_id=message["message_id"],
                linked_event=message["reply_to_message"]["message_id"],
                target=message["chat"]["id"],
                connector=self,
                raw_event=message,
            )

        if message.get("photo") or message.get("document") or message.get("video"):
            _LOGGER.debug(
                _("Received image/file/video from Telegram, unable to parse this data.")
            )
            return

        if message.get("text"):
            event = Message(
                text=emoji.demojize(message["text"]),
                user=user,
                user_id=user_id,
                target=message["chat"]["id"],
                connector=self,
            )

        if message.get("location"):
            event = telegram_events.Location(
                user=user,
                user_id=user_id,
                event_id=update_id,
                target=message["chat"]["id"],
                location=message["location"],
                connector=self,
                raw_event=message,
            )

        if message.get("poll"):
            event = telegram_events.Poll(
                user=user,
                user_id=user_id,
                event_id=update_id,
                target=message["chat"]["id"],
                poll=message["poll"],
                connector=self,
                raw_event=message,
            )

        if message.get("contact"):
            event = telegram_events.Contact(
                user=user,
                user_id=user_id,
                event_id=update_id,
                target=message["chat"]["id"],
                contact=message["contact"],
                connector=self,
                raw_event=message,
            )

        return event

    async def listen(self):
        """Listen method of the connector.

        Since we are using webhooks, we don't need to implement the listen
        method.

        """

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message.

        Args:
            message (object): An instance of Message.

        """
        _LOGGER.debug(
            _("Responding with: '%s' at target: '%s'"), message.text, message.target
        )

        data = dict()
        data["chat_id"] = message.target
        data["text"] = message.text

        async with aiohttp.ClientSession() as session:
            resp = await session.post(self.build_url("sendMessage"), data=data)
            if resp.status == 200:
                _LOGGER.debug(_("Successfully responded."))
            else:
                _LOGGER.error(_("Unable to respond."))

    @register_event(Image)
    async def send_image(self, file_event):
        """Send Image to Telegram.

        Gets the chat id from the channel and then
        sends the bytes of the image as multipart/form-data.

        """
        data = aiohttp.FormData()
        data.add_field(
            "chat_id", str(file_event.target["id"]), content_type="multipart/form-data"
        )
        data.add_field(
            "photo",
            await file_event.get_file_bytes(),
            content_type="multipart/form-data",
        )

        resp = await self.session.post(self.build_url("sendPhoto"), data=data)
        if resp.status == 200:
            _LOGGER.debug(_("Sent %s image successfully."), file_event.name)
        else:
            _LOGGER.debug(_("Unable to send image - Status Code %s."), resp.status)

    @register_event(File)
    async def send_file(self, file_event):
        """Send File to Telegram.

        Gets the chat id from the channel and then
        sends the bytes of the file as multipart/form-data.

        """
        data = aiohttp.FormData()
        data.add_field(
            "chat_id", str(file_event.target["id"]), content_type="multipart/form-data"
        )
        data.add_field(
            "document",
            await file_event.get_file_bytes(),
            content_type="multipart/form-data",
        )

        resp = await self.session.post(self.build_url("sendDocument"), data=data)
        if resp.status == 200:
            _LOGGER.debug(_("Sent %s file successfully."), file_event.name)
        else:
            _LOGGER.debug(_("Unable to send file - Status Code %s."), resp.status)

    async def disconnect(self):
        """Disconnect from Telegram.

        Stops the infinite loop found in self._listen(), closes
        aiohttp session.

        """
        await self.delete_webhook()

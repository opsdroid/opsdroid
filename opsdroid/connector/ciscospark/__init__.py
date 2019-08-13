"""A connector for Cisco Spark."""
import json
import logging
import uuid

import aiohttp

from ciscosparkapi import CiscoSparkAPI

from opsdroid.connector import Connector
from opsdroid.message import Message


_LOGGER = logging.getLogger(__name__)


class ConnectorCiscoSpark(Connector):
    """A connector for Cisco Spark."""

    def __init__(self, config):
        """Create a connector."""
        _LOGGER.debug("Starting cisco spark connector")
        self.name = "ciscospark"
        self.config = config
        self.opsdroid = None
        self.default_room = None
        self.bot_name = config.get("bot-name", "opsdroid")
        self.bot_spark_id = None
        self.secret = uuid.uuid4().hex
        self.people = {}

    async def connect(self, opsdroid):
        """Connect to the chat service."""
        self.opsdroid = opsdroid
        try:
            self.api = CiscoSparkAPI(access_token=self.config["access-token"])
        except KeyError:
            _LOGGER.error("Must set accesst-token for cisco spark connector!")
            return

        await self.clean_up_webhooks()
        await self.subscribe_to_rooms()
        await self.set_own_id()

    async def ciscospark_message_handler(self, request):
        """Handle webhooks from the Cisco api."""
        _LOGGER.debug("Handling message from Cisco Spark")
        req_data = await request.json()

        _LOGGER.debug(req_data)

        msg = self.api.messages.get(req_data["data"]["id"])

        if req_data["data"]["personId"] != self.bot_spark_id:
            person = await self.get_person(req_data["data"]["personId"])

            try:
                message = Message(
                    msg.text,
                    person.displayName,
                    {"id": msg.roomId, "type": msg.roomType},
                    self,
                )
                await self.opsdroid.parse(message)
            except KeyError as error:
                _LOGGER.error(error)

        return aiohttp.web.Response(text=json.dumps("Received"), status=201)

    async def clean_up_webhooks(self):
        """Remove all existing webhooks."""
        for webhook in self.api.webhooks.list():
            self.api.webhooks.delete(webhook.id)

    async def subscribe_to_rooms(self):
        """Create webhooks for all rooms."""
        _LOGGER.debug("Creating Cisco Spark webhook")
        webhook_endpoint = "/connector/ciscospark"
        self.opsdroid.web_server.web_app.router.add_post(
            webhook_endpoint, self.ciscospark_message_handler
        )

        self.api.webhooks.create(
            name="opsdroid",
            targetUrl="{}{}".format(self.config.get("webhook-url"), webhook_endpoint),
            resource="messages",
            event="created",
            secret=self.secret,
        )

    async def get_person(self, personId):
        """Get a person's info from the api or cache."""
        if personId not in self.people:
            self.people[personId] = self.api.people.get(personId)
        return self.people[personId]

    async def set_own_id(self):
        """Get the bot id and set it in the class."""
        self.bot_spark_id = self.api.people.me().id

    async def listen(self, opsdroid):
        """Listen for and parse new messages."""
        pass  # Listening is handled by the aiohttp web server

    async def respond(self, message, room=None):
        """Respond with a message."""
        self.api.messages.create(message.room["id"], text=message.text)

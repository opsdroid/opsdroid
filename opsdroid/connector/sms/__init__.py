#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Opsdroid Imports
from opsdroid.connector import Connector, register_event
from opsdroid.events import Message
import logging

# Twilio Imports
from twilio.rest import Client

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    "name": str,
    "account_sid": str,
    "auth_token": str,
    "phone_number": str,
    "host": str,
    "port": int,
}


class SMSConnector(Connector):
    """A connector for Twilio-powered SMS"""

    def __init__(self, config, opsdroid):
        super().__init__(config, opsdroid=opsdroid)
        self.name = config["name"]
        self.config = config

    async def connect(self):
        """Connect to Twilio and setup webhooks"""
        self.connection = await Client(
            self.config["account_sid"], self.config["auth_token"]
        )
        self.opsdroid.web_server.web_app.router.add_get(
            f"/connector/{self.name}", self.handle_messages
        )

    async def handle_messages(self, request):
        req_data = await request.json()
        try:
            message = Message(req_data["Body"], req_data["From"], None, self,)
            await self.opsdroid.parse(message)
        except Exception as e:
            _LOGGER.error(f"ERROR: {e}")

    @register_event(Message)
    async def send_message(self, message):
        try:
            self.connection.messages.create(
                from_=self.config["number"], to=message.user, body=message.text
            )
        except Exception as e:
            _LOGGER.error(
                f"{str(self.name).upper} COULD NOT SEND MESSAGE \n [ERROR]: {e}"
            )

    async def listen(self):
        pass

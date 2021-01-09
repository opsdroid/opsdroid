'''A SMS connector for opsdroid'''
import asyncio
import logging

from twilio.rest import Client
from voluptuous import Required

from .. import Connector, register_event
from ...events import Message

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = {
    "name": str,
    Required("account_sid"): str,
    Required("auth_token"): str,
    Required("phone_number"): str,
    Required("is_trial"): bool,
    "approved_trial_numbers": list,
}


class SMSConnectorException(Exception):
    ...


class ConnectorSMS(Connector):
    """A connector for SMS."""

    def __init__(self, config, opsdroid):
        super().__init__(config, opsdroid=opsdroid)
        self.name = self.config.get("name", "sms")
        self.bot_name = config.get("bot-name", "opsdroid")
        self.config = config

        if self.config['is_trial'] and not config.get('approved_trial_numbers'):
            raise SMSConnectorException('Please set approved_trial_numbers')

    async def connect(self):
        """Connect to Twilio and setup webhooks"""
        self.connection = await asyncio.get_running_loop().run_in_executor(
            None,
            Client,
            self.config["account_sid"],
            self.config["auth_token"]
        )
        self.opsdroid.web_server.web_app.router.add_post(
            f"/connector/{self.name}", self.handle_messages
        )

    async def handle_messages(self, request):
        req_data = await request.post()
        message = Message(
            text=req_data["Body"],
            user=req_data["From"],
            user_id=req_data["From"],
            connector=self,
        )
        await self.opsdroid.parse(message)

    @register_event(Message)
    async def send_message(self, message):
        if (
            self.config["is_trial"]
            and message.user not in self.config["allowed_trial_users"]
        ):
            _LOGGER.error(
                "[ERROR] This number is not verified for use with your Twilio Trial Account"
            )
        else:
            await asyncio.get_running_loop().run_in_executor(
                self.connection.messages.create,
                from_=self.config["phone_number"],
                to=message.user,
                body=message.text
            )

    async def listen(self):
        pass

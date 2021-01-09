'''A SMS connector for opsdroid'''
import aiohttp.web
import asyncio
import functools
import logging

from twilio.rest import Client
from twilio.request_validator import RequestValidator
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

        self.validator = RequestValidator(config.get('auth_token'))

    async def connect(self):
        """Connect to Twilio and setup webhooks"""
        self.connection = await asyncio.get_running_loop().run_in_executor(
            None,
            Client,
            self.config["account_sid"],
            self.config["auth_token"]
        )
        # This route must be configured manually in the Twilio web GUI.
        # There is no API for configuring it.
        # Watch this SO post for any developments.
        # Last updated by Twilio as of August 2019.
        # https://stackoverflow.com/a/57420558/1221924
        self.opsdroid.web_server.web_app.router.add_post(
            f"/connector/{self.name}", self.handle_messages
        )

    async def handle_messages(self, request):
        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        data = await request.post()
        request_valid = self.validator.validate(
            str(request.url),
            data,
            request.headers.get('X-TWILIO-SIGNATURE', ''))
        if not request_valid:
            raise aiohttp.web.HTTPForbidden()
        message = Message(
            text=data["Body"],
            user=data["From"],
            user_id=data["From"],
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
                None,
                # run_in_executor only accepts positional arguments, so
                # partial is used here to pass in kwargs.
                functools.partial(
                    self.connection.messages.create,
                    from_=self.config["phone_number"],
                    to=message.user,
                    body=message.text
                )
            )

    async def listen(self):
        pass

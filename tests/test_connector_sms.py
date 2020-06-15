import unittest
import asyncio

import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.connector.sms import ConnectorSMS
from opsdroid.cli.start import configure_lang


class TestConnectorSMS(unittest.TestCase):
    """Test the opsdroid SMS connector class."""

    def setUp(self):
        self.loop = asyncio.new_event_loop()

    def test_init(self):
        opsdroid = amock.CoroutineMock()
        connector = ConnectorSMS({}, opsdroid=opsdroid)
        self.assertEqual("sms", connector.name)

    def test_property(self):
        opsdroid = amock.CoroutineMock()
        connector = ConnectorSMS({}, opsdroid=opsdroid)
        self.assertEqual("sms", connector.name)


class TestConnectorSMSAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid SMS connector class."""

    async def setUp(self):
        configure_lang({})

    async def test_connect(self):
        """Test the connect method adds the handlers."""
        opsdroid = amock.CoroutineMock()
        connector = ConnectorSMS({}, opsdroid=opsdroid)
        opsdroid.web_server = amock.CoroutineMock()
        opsdroid.web_server.web_app = amock.CoroutineMock()
        opsdroid.web_server.web_app.router = amock.CoroutineMock()
        opsdroid.web_server.web_app.router.add_get = amock.CoroutineMock()

        await connector.connect()

        self.assertTrue(opsdroid.web_server.web_app.router.add_get.called)

    async def test_message_handler(self):
        """Test the message handler."""

        opsdroid = amock.CoroutineMock()
        connector = ConnectorSMS({}, opsdroid=opsdroid)
        req_ob = {
            "From": "555-555-5555",
            "Body": "Join Earth's Mightiests Heros. Like Kevin Bacon",
        }
        mock_request = amock.CoroutineMock()
        mock_request.json = amock.CoroutineMock()
        mock_request.json.return_value = req_ob

        with OpsDroid() as opsdroid:
            connector.opsdroid = opsdroid
            connector.opsdroid.parse = amock.CoroutineMock()

            await connector.handle_messages(mock_request)
            self.assertTrue(connector.opsdroid.parse.called)

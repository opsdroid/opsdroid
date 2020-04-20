import os.path

import asyncio
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock
from tweepy import OAuthHandler

from opsdroid.core import OpsDroid
from opsdroid.connector.twitter import ConnectorTwitter, StdOutListener
import json


class TestStdOutListener(unittest.TestCase):
    def test_init(self):
        connector = 1

    def test_on_connect(self):
        connector = StdOutListener(OpsDroid(), ConnectorTwitter({"name": ""}))
        connector.on_connect()
        self.assertLogs("_LOGGER", "debug")

    def test_on_disconnect(self):
        connector = StdOutListener(OpsDroid(), ConnectorTwitter({"name": ""}))
        connector.on_disconnect("connecting")
        self.assertLogs("_LOGGER", "debug")

    def test_on_data_with_enable_dms_false(self):
        connector = ConnectorTwitter({"enable_dms": True})
        connector.process_dm = amock.CoroutineMock()
        connector.screen_name = "test_screen1"
        status = json.dumps(
            {"direct_message": {"sender": {"screen_name": "test_screen"}}}
        )
        std_connector = StdOutListener(OpsDroid(), connector)
        self.assertEqual(std_connector.on_data(status), True)
        self.assertTrue(connector.process_dm.called)

    def test_on_data_with_enable_tweets_false(self):
        connector = ConnectorTwitter({"enable_tweets": True})
        connector.process_tweet = amock.CoroutineMock()
        connector.screen_name = "test_screen1"
        status = json.dumps(
            {
                "user": {"screen_name": "test_screen"},
                "id": "",
                "created_at": "",
                "text": "",
            }
        )
        std_connector = StdOutListener(OpsDroid(), connector)
        self.assertEqual(std_connector.on_data(status), True)
        self.assertTrue(connector.process_tweet.called)

    def test_on_error(self):
        status = json.dumps({"user": {"screen_name": "test_screen"}})
        connector = StdOutListener(OpsDroid(), ConnectorTwitter({"name": ""}))
        connector.on_error(status)
        self.assertLogs("_LOGGER", "info")


class TestConnectorTwitter(asynctest.TestCase):
    def setUp(self):
        self.connector = ConnectorTwitter(
            {
                "consumer_key": "testconsumerkey",
                "consumer_secret": "testconsumersecret",
                "oauth_token": "testoauthtoken",
                "oauth_token_secret": "testoauthtokensecret",
            }
        )
        self.connector.opsdroid = amock.CoroutineMock()
        self.connector.opsdroid.eventloop.run_in_executor = amock.CoroutineMock()
        self.connector.opsdroid.eventloop.create_task = amock.CoroutineMock()
        self.connector.opsdroid.parse = amock.CoroutineMock()
        self.connector.auth = amock.CoroutineMock()
        self.connector.auth.get_username = amock.CoroutineMock()
        self.connector.auth.get_username.name.return_value = ""

    @amock.patch("opsdroid.connector.twitter.API")
    async def test_connect(self,mocked_api):
        await self.connector.connect(OpsDroid())
        self.assertLogs("_LOGGER", "debug")

    @amock.patch("opsdroid.connector.twitter.Stream")
    async def test_listen(self, mocked_stream):
        await self.connector.listen(self.connector.opsdroid)
        self.assertTrue(self.connector.opsdroid.eventloop.run_in_executor.called)

    async def test_clean_tweet(self):
        assert("testtweet",self.connector.clean_tweet("test@{}tweet "))

    def test_process_tweet(self):
        dm = {"text":"1","user":{"screen_name":"2"},"id":"3"}
        self.connector.process_tweet(dm)
        self.assertLogs("_LOGGER", "debug")
        self.assertTrue(self.connector.opsdroid.parse.called)
        self.assertTrue(self.connector.opsdroid.eventloop.create_task.called)

    def test_process_dm(self):
        dm = {"text":"1","sender":{"screen_name":"2"},"id":"3"}
        self.connector.process_dm(dm)
        self.assertLogs("_LOGGER", "debug")
        self.assertTrue(self.connector.opsdroid.parse.called)
        self.assertTrue(self.connector.opsdroid.eventloop.create_task.called)









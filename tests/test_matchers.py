
import asynctest
import asynctest.mock as mock

import aiohttp.web

from opsdroid.core import OpsDroid
from opsdroid.web import Web
from opsdroid import matchers


class TestMatchers(asynctest.TestCase):
    """Test the opsdroid matcher decorators."""

    async def test_match_regex(self):
        with OpsDroid() as opsdroid:
            regex = r"(.*)"
            mockedskill = mock.MagicMock()
            decorator = matchers.match_regex(regex)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["regex"]["expression"], regex)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)

    async def test_match_apiai(self):
        with OpsDroid() as opsdroid:
            action = "myaction"
            mockedskill = mock.MagicMock()
            decorator = matchers.match_apiai_action(action)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["dialogflow_action"], action)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)
            intent = "myIntent"
            decorator = matchers.match_apiai_intent(intent)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 2)
            self.assertEqual(opsdroid.skills[1]["dialogflow_intent"], intent)
            self.assertIsInstance(opsdroid.skills[1]["skill"], mock.MagicMock)
            with mock.patch('opsdroid.matchers._LOGGER.warning') as logmock:
                decorator = matchers.match_apiai_intent(intent)
                decorator(mockedskill)
                self.assertTrue(logmock.called)

    async def test_match_dialogflow(self):
        with OpsDroid() as opsdroid:
            action = "myaction"
            mockedskill = mock.MagicMock()
            decorator = matchers.match_dialogflow_action(action)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["dialogflow_action"], action)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)
            intent = "myIntent"
            decorator = matchers.match_dialogflow_intent(intent)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 2)
            self.assertEqual(opsdroid.skills[1]["dialogflow_intent"], intent)
            self.assertIsInstance(opsdroid.skills[1]["skill"], mock.MagicMock)

    async def test_match_luisai(self):
        with OpsDroid() as opsdroid:
            intent = "myIntent"
            mockedskill = mock.MagicMock()
            decorator = matchers.match_luisai_intent(intent)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["luisai_intent"], intent)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)

    async def test_match_witai(self):
        with OpsDroid() as opsdroid:
            intent = "myIntent"
            mockedskill = mock.MagicMock()
            decorator = matchers.match_witai(intent)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["witai_intent"], intent)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)

    async def test_match_crontab(self):
        with OpsDroid() as opsdroid:
            crontab = "* * * * *"
            mockedskill = mock.MagicMock()
            decorator = matchers.match_crontab(crontab)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["crontab"], crontab)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)

    async def test_match_webhook(self):
        with OpsDroid() as opsdroid:
            opsdroid.loader.current_import_config = {"name": "testhook"}
            opsdroid.web_server = Web(opsdroid)
            opsdroid.web_server.web_app = mock.Mock()
            webhook = "test"
            mockedskill = mock.MagicMock()
            decorator = matchers.match_webhook(webhook)
            decorator(mockedskill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["webhook"], webhook)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)
            self.assertEqual(
                opsdroid.web_server.web_app.router.add_post.call_count, 2)

    async def test_match_webhook_response(self):
        with OpsDroid() as opsdroid:
            opsdroid.loader.current_import_config = {"name": "testhook"}
            opsdroid.web_server = Web(opsdroid)
            opsdroid.web_server.web_app = mock.Mock()
            webhook = "test"
            mockedskill = mock.CoroutineMock()
            decorator = matchers.match_webhook(webhook)
            decorator(mockedskill)
            postcalls, _ = \
                opsdroid.web_server.web_app.router.add_post.call_args_list[0]
            wrapperfunc = postcalls[1]
            webhookresponse = await wrapperfunc(None)
            self.assertEqual(type(webhookresponse), aiohttp.web.Response)

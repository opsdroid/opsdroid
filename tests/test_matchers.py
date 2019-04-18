
import asynctest
import asynctest.mock as mock

import asyncio
import aiohttp.web

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.web import Web
from opsdroid import matchers


class TestMatchers(asynctest.TestCase):
    """Test the opsdroid matcher decorators."""

    async def setUp(self):
        configure_lang({})

    async def getMockSkill(self):
        async def mockedskill(opsdroid, config, message):
            pass
        return mockedskill

    async def getMockWebSkill(self):
        async def mockedwebskill(opsdroid, config, message):
            return aiohttp.web.Response(body=b'custom response', status=200)
        return mockedwebskill

    async def test_match_regex(self):
        with OpsDroid() as opsdroid:
            regex = r"(.*)"
            decorator = matchers.match_regex(regex)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0].matchers[0]["regex"]["expression"], regex)
            self.assertTrue(asyncio.iscoroutinefunction(opsdroid.skills[0]))

    async def test_match_apiai(self):
        with OpsDroid() as opsdroid:
            action = "myaction"
            decorator = matchers.match_apiai_action(action)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0].matchers[0]["dialogflow_action"], action)
            self.assertTrue(asyncio.iscoroutinefunction(opsdroid.skills[0]))
            intent = "myIntent"
            decorator = matchers.match_apiai_intent(intent)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            self.assertEqual(len(opsdroid.skills), 2)
            self.assertEqual(opsdroid.skills[1].matchers[0]["dialogflow_intent"], intent)
            self.assertTrue(asyncio.iscoroutinefunction(opsdroid.skills[1]))
            decorator = matchers.match_apiai_intent(intent)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            self.assertLogs('_LOGGER', 'warning')

    async def test_match_dialogflow(self):
        with OpsDroid() as opsdroid:
            action = "myaction"
            decorator = matchers.match_dialogflow_action(action)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0].matchers[0]["dialogflow_action"], action)
            self.assertTrue(asyncio.iscoroutinefunction(opsdroid.skills[0]))
            intent = "myIntent"
            decorator = matchers.match_dialogflow_intent(intent)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            self.assertEqual(len(opsdroid.skills), 2)
            self.assertEqual(opsdroid.skills[1].matchers[0]["dialogflow_intent"], intent)
            self.assertTrue(asyncio.iscoroutinefunction(opsdroid.skills[1]))

    async def test_match_luisai(self):
        with OpsDroid() as opsdroid:
            intent = "myIntent"
            decorator = matchers.match_luisai_intent(intent)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0].matchers[0]["luisai_intent"], intent)
            self.assertTrue(asyncio.iscoroutinefunction(opsdroid.skills[0]))

    async def test_match_witai(self):
        with OpsDroid() as opsdroid:
            intent = "myIntent"
            decorator = matchers.match_witai(intent)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0].matchers[0]["witai_intent"], intent)
            self.assertTrue(asyncio.iscoroutinefunction(opsdroid.skills[0]))

    async def test_match_rasanu(self):
        with OpsDroid() as opsdroid:
            intent = "myIntent"
            decorator = matchers.match_rasanlu(intent)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0].matchers[0]["rasanlu_intent"], intent)
            self.assertTrue(asyncio.iscoroutinefunction(opsdroid.skills[0]))

    async def test_match_recastai(self):
        with OpsDroid() as opsdroid:
            intent = "myIntent"
            decorator = matchers.match_recastai(intent)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0].matchers[0]["sapcai_intent"], intent)
            self.assertTrue(asyncio.iscoroutinefunction(opsdroid.skills[0]))
            self.assertLogs("Warning", "_LOGGER")

    async def test_match_crontab(self):
        with OpsDroid() as opsdroid:
            crontab = "* * * * *"
            decorator = matchers.match_crontab(crontab)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0].matchers[0]["crontab"], crontab)
            self.assertTrue(asyncio.iscoroutinefunction(opsdroid.skills[0]))

    async def test_match_webhook(self):
        with OpsDroid() as opsdroid:
            opsdroid.loader.current_import_config = {"name": "testhook"}
            opsdroid.web_server = Web(opsdroid)
            opsdroid.web_server.web_app = mock.Mock()
            webhook = "test"
            decorator = matchers.match_webhook(webhook)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            opsdroid.skills[0].config = {"name": "mockedskill"}
            opsdroid.web_server.setup_webhooks(opsdroid.skills)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0].matchers[0]["webhook"], webhook)
            self.assertTrue(asyncio.iscoroutinefunction(opsdroid.skills[0]))
            self.assertEqual(
                opsdroid.web_server.web_app.router.add_post.call_count, 2)

    async def test_match_webhook_response(self):
        with OpsDroid() as opsdroid:
            opsdroid.loader.current_import_config = {"name": "testhook"}
            opsdroid.web_server = Web(opsdroid)
            opsdroid.web_server.web_app = mock.Mock()
            webhook = "test"
            decorator = matchers.match_webhook(webhook)
            opsdroid.skills.append(decorator(await self.getMockSkill()))
            opsdroid.skills[0].config = {"name": "mockedskill"}
            opsdroid.web_server.setup_webhooks(opsdroid.skills)
            postcalls, _ = \
                opsdroid.web_server.web_app.router.add_post.call_args_list[0]
            wrapperfunc = postcalls[1]
            webhookresponse = await wrapperfunc(None)
            self.assertEqual(type(webhookresponse), aiohttp.web.Response)

    async def test_match_webhook_custom_response(self):
        with OpsDroid() as opsdroid:
            opsdroid.loader.current_import_config = {"name": "testhook"}
            opsdroid.web_server = Web(opsdroid)
            opsdroid.web_server.web_app = mock.Mock()
            webhook = "test"
            decorator = matchers.match_webhook(webhook)
            opsdroid.skills.append(decorator(await self.getMockWebSkill()))
            opsdroid.skills[0].config = {"name": "mockedskill"}
            opsdroid.web_server.setup_webhooks(opsdroid.skills)
            postcalls, _ = \
                opsdroid.web_server.web_app.router.add_post.call_args_list[0]
            wrapperfunc = postcalls[1]
            webhookresponse = await wrapperfunc(None)
            self.assertEqual(type(webhookresponse), aiohttp.web.Response)
            self.assertEqual(webhookresponse.body, b'custom response')


import asyncio
import asynctest
import asynctest.mock as amock

from aiohttp import ClientOSError

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_dialogflow_action
from opsdroid.events import Message
from opsdroid.parsers import dialogflow
from opsdroid.connector import Connector


class TestParserDialogflow(asynctest.TestCase):
    """Test the opsdroid Dialogflow parser."""

    async def setup(self):
        configure_lang({})

    async def getMockSkill(self):
        async def mockedskill(opsdroid, config, message):
            pass
        mockedskill.config = {}
        return mockedskill

    async def getRaisingMockSkill(self):
        async def mockedskill(opsdroid, config, message):
            raise Exception()
        mockedskill.config = {}
        return mockedskill

    async def test_call_dialogflow(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        message = Message("Hello world", "user", "default", mock_connector)
        config = {'name': 'dialogflow', 'access-token': 'test'}
        result = amock.Mock()
        result.json = amock.CoroutineMock()
        result.json.return_value = {
                "result": {
                    "action": "myaction",
                    "score": 0.7
                },
                "status": {
                    "code": 200,
                    "errorType": "success"
                }
            }
        with amock.patch('aiohttp.ClientSession.post') as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)

            await dialogflow.call_dialogflow(message, config)
            self.assertTrue(patched_request.called)

    async def test_parse_dialogflow(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {'name': 'dialogflow', 'access-token': "test"}
                ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {
                "name": "greetings"
            }
            opsdroid.skills.append(match_dialogflow_action('myaction')(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(dialogflow, 'call_dialogflow') as \
                    mocked_call_dialogflow:
                mocked_call_dialogflow.return_value = {
                        "result": {
                            "action": "myaction",
                            "score": 0.7
                        },
                        "status": {
                            "code": 200,
                            "errorType": "success"
                        }
                    }
                skills = await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])
                self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_dialogflow_raises(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {'name': 'dialogflow', 'access-token': "test"}
                ]
            mock_skill = await self.getRaisingMockSkill()
            mock_skill.config = {
                "name": "greetings"
            }
            opsdroid.skills.append(match_dialogflow_action('myaction')(mock_skill))

            mock_connector = amock.MagicMock()
            mock_connector.send = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(dialogflow, 'call_dialogflow') as \
                    mocked_call_dialogflow:
                mocked_call_dialogflow.return_value = {
                        "result": {
                            "action": "myaction",
                            "score": 0.7
                        },
                        "status": {
                            "code": 200,
                            "errorType": "success"
                        }
                    }
                skills = await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])
                self.assertEqual(mock_skill, skills[0]["skill"])

            await opsdroid.run_skill(
                skills[0]["skill"], skills[0]["config"], message
            )
            self.assertLogs('_LOGGER', 'exception')

    async def test_parse_dialogflow_failure(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {'name': 'dialogflow', 'access-token': "test"}
                ]
            mock_skill = amock.CoroutineMock()
            match_dialogflow_action('myaction')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(dialogflow, 'call_dialogflow') as \
                    mocked_call_dialogflow:
                mocked_call_dialogflow.return_value = {
                        "result": {
                            "action": "myaction",
                            "score": 0.7
                        },
                        "status": {
                            "code": 404,
                            "errorType": "not found"
                        }
                    }
                skills = await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])
                self.assertFalse(skills)

    async def test_parse_dialogflow_low_score(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {
                        'name': 'dialogflow',
                        'access-token': "test",
                        "min-score": 0.8
                    }
                ]
            mock_skill = amock.CoroutineMock()
            match_dialogflow_action('myaction')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(dialogflow, 'call_dialogflow') as \
                    mocked_call_dialogflow:
                mocked_call_dialogflow.return_value = {
                        "result": {
                            "action": "myaction",
                            "score": 0.7
                        },
                        "status": {
                            "code": 200,
                            "errorType": "success"
                        }
                    }
                await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])

            self.assertFalse(mock_skill.called)

    async def test_parse_dialogflow_raise_ClientOSError(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {
                        'name': 'dialogflow',
                        'access-token': "test",
                        "min-score": 0.8}
                ]
            mock_skill = amock.CoroutineMock()
            match_dialogflow_action('myaction')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(dialogflow, 'call_dialogflow') \
                    as mocked_call:
                mocked_call.side_effect = ClientOSError()
                await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])

            self.assertFalse(mock_skill.called)
            self.assertTrue(mocked_call.called)

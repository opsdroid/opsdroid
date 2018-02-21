
import asyncio
import asynctest
import asynctest.mock as amock

from aiohttp import ClientOSError

from opsdroid.core import OpsDroid
from opsdroid.matchers import match_luisai_intent
from opsdroid.message import Message
from opsdroid.parsers import luisai
from opsdroid.connector import Connector


class TestParserLuisai(asynctest.TestCase):
    """Test the opsdroid luis.ai parser."""

    async def test_call_luisai(self):
        mock_connector = Connector({})
        message = Message("schedule meeting", "user", "default",
                          mock_connector)
        config = {'name': 'luisai',
                  'appid': 'test',
                  'appkey': 'test',
                  'verbose': True}
        result = amock.Mock()
        result.json = amock.CoroutineMock()
        result.json.return_value = {
                "query": "schedule meeting",
                "topScoringIntent": {
                    "intent": "Calendar.Add",
                    "score": 0.900492251
                },
                "intents": [
                    {
                        "intent": "Calendar.Add",
                        "score": 0.900492251
                    }
                ],
                "entities": []
            }
        with amock.patch('aiohttp.ClientSession.get') as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            await luisai.call_luisai(message, config)
            self.assertTrue(patched_request.called)

    async def test_parse_luisai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {'name': 'luisai',
                     'appid': 'test',
                     'appkey': 'test',
                     'verbose': True}
                ]
            mock_skill = amock.CoroutineMock()
            match_luisai_intent('Calendar.Add')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("schedule meeting", "user", "default",
                              mock_connector)

            with amock.patch.object(luisai, 'call_luisai') as \
                    mocked_call_luisai:
                mocked_call_luisai.return_value = {
                        "query": "schedule meeting",
                        "topScoringIntent": {
                            "intent": "Calendar.Add",
                            "score": 0.900492251
                        },
                        "intents": [
                            {
                                "intent": "Calendar.Add",
                                "score": 0.900492251
                            }
                        ],
                        "entities": []
                    }
                skills = await luisai.parse_luisai(
                    opsdroid, message, opsdroid.config['parsers'][0])
                self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_luisai_raises(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {'name': 'luisai',
                     'appid': 'test',
                     'appkey': 'test',
                     'verbose': True}
                ]
            mock_skill = amock.CoroutineMock()
            mock_skill.side_effect = Exception()
            opsdroid.loader.current_import_config = {
                "name": "mocked-skill"
            }
            match_luisai_intent('Calendar.Add')(mock_skill)

            mock_connector = amock.MagicMock()
            mock_connector.respond = amock.CoroutineMock()
            message = Message("schedule meeting", "user", "default",
                              mock_connector)

            with amock.patch.object(luisai, 'call_luisai') as \
                    mocked_call_luisai:
                mocked_call_luisai.return_value = {
                        "query": "schedule meeting",
                        "topScoringIntent": {
                            "intent": "Calendar.Add",
                            "score": 0.900492251
                        },
                        "intents": [
                            {
                                "intent": "Calendar.Add",
                                "score": 0.900492251
                            }
                        ],
                        "entities": []
                    }
                skills = await luisai.parse_luisai(
                    opsdroid, message, opsdroid.config['parsers'][0])
                self.assertEqual(mock_skill, skills[0]["skill"])

            await opsdroid.run_skill(
                skills[0]["skill"], skills[0]["config"], message)
            self.assertTrue(skills[0]["skill"].called)

    async def test_parse_luisai_failure(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {'name': 'luisai',
                     'appid': 'test',
                     'appkey': 'test',
                     'verbose': True}
                ]
            mock_skill = amock.CoroutineMock()
            match_luisai_intent('Calendar.Add')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("schedule meeting", "user", "default",
                              mock_connector)

            with amock.patch.object(luisai, 'call_luisai') as \
                    mocked_call_luisai:
                mocked_call_luisai.return_value = {
                        "statusCode": 401
                    }
                skills = await luisai.parse_luisai(
                    opsdroid, message, opsdroid.config['parsers'][0])
                self.assertFalse(skills)

    async def test_parse_luisai_low_score(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {'name': 'luisai',
                     'appid': 'test',
                     'appkey': 'test',
                     'verbose': True,
                     'min-score': 0.95}
                ]
            mock_skill = amock.CoroutineMock()
            match_luisai_intent('Calendar.Add')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("schedule meeting", "user", "default",
                              mock_connector)

            with amock.patch.object(luisai, 'call_luisai') as \
                    mocked_call_luisai:
                mocked_call_luisai.return_value = {
                        "query": "schedule meeting",
                        "topScoringIntent": {
                            "intent": "Calendar.Add",
                            "score": 0.900492251
                        },
                        "intents": [
                            {
                                "intent": "Calendar.Add",
                                "score": 0.900492251
                            }
                        ],
                        "entities": []
                    }
                await luisai.parse_luisai(opsdroid, message,
                                          opsdroid.config['parsers'][0])

            self.assertFalse(mock_skill.called)

    async def test_parse_luisai_raise_ClientOSError(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {'name': 'luisai',
                     'appid': 'test',
                     'appkey': 'test',
                     'verbose': True,
                     'min-score': 0.95}
                ]
            mock_skill = amock.CoroutineMock()
            match_luisai_intent('Calendar.Add')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("schedule meeting", "user", "default",
                              mock_connector)

            with amock.patch.object(luisai, 'call_luisai') as \
                    mocked_call:
                mocked_call.side_effect = ClientOSError()
                await luisai.parse_luisai(opsdroid, message,
                                          opsdroid.config['parsers'][0])

            self.assertFalse(mock_skill.called)
            self.assertTrue(mocked_call.called)

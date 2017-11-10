import asynctest
import asynctest.mock as amock

from aiohttp import helpers, ClientOSError

from opsdroid.core import OpsDroid
from opsdroid.matchers import match_rasanlu
from opsdroid.message import Message
from opsdroid.parsers import rasanlu
from opsdroid.connector import Connector


class TestParserRasaNLU(asynctest.TestCase):
    """Test the opsdroid Rasa NLU parser."""

    async def test_call_rasanlu(self):
        mock_connector = Connector({})
        message = Message("how's the weather outside", "user",
                          "default", mock_connector)
        config = {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
        result = amock.Mock()
        result.status = 200
        result.json = amock.CoroutineMock()
        result.json.return_value = {
            "entities": [
                {
                    "end": 32,
                    "entity": "state",
                    "extractor": "ner_crf",
                    "start": 25,
                    "value": "running"
                }
            ],
            "intent": {
                "confidence": 0.5745766766665303,
                "name": "get_weather"
            },
            "intent_ranking": [
                {
                    "confidence": 0.5745766766665303,
                    "name": "get_weather"
                },
                {
                    "confidence": 0.42542332333346977,
                    "name": "other_weather"
                }
            ],
            "text": "how's the weather outside"
        }
        with amock.patch('aiohttp.ClientSession.post') as patched_request:
            patched_request.return_value = helpers.create_future(self.loop)
            patched_request.return_value.set_result(result)
            await rasanlu.call_rasanlu(message.text, config)
            self.assertTrue(patched_request.called)

    async def test_parse_rasanlu(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            match_rasanlu('get_weather')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("how's the weather outside", "user",
                              "default", mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') as mocked_call_rasanlu:
                mocked_call_rasanlu.return_value = {
                    "entities": [
                        {
                            "end": 32,
                            "entity": "state",
                            "extractor": "ner_crf",
                            "start": 25,
                            "value": "running"
                        }
                    ],
                    "intent": {
                        "confidence": 0.9745766766665303,
                        "name": "get_weather"
                    },
                    "intent_ranking": [
                        {
                            "confidence": 0.9745766766665303,
                            "name": "get_weather"
                        },
                        {
                            "confidence": 0.42542332333346977,
                            "name": "other_weather"
                        }
                    ],
                    "text": "how's the weather outside"
                }
                skills = await rasanlu.parse_rasanlu(
                    opsdroid, message, opsdroid.config['parsers'][0])
                self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_rasanlu_raises(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            mock_skill.side_effect = Exception()
            opsdroid.loader.current_import_config = {
                "name": "mocked-skill"
            }
            match_rasanlu('get_weather')(mock_skill)

            mock_connector = amock.MagicMock()
            mock_connector.respond = amock.CoroutineMock()
            message = Message("how's the weather outside", "user",
                              "default", mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') as mocked_call_rasanlu:
                mocked_call_rasanlu.return_value = {
                    "entities": [
                        {
                            "end": 32,
                            "entity": "state",
                            "extractor": "ner_crf",
                            "start": 25,
                            "value": "running"
                        }
                    ],
                    "intent": {
                        "confidence": 0.9745766766665303,
                        "name": "get_weather"
                    },
                    "intent_ranking": [
                        {
                            "confidence": 0.9745766766665303,
                            "name": "get_weather"
                        },
                        {
                            "confidence": 0.42542332333346977,
                            "name": "other_weather"
                        }
                    ],
                    "text": "how's the weather outside"
                }
                skills = await rasanlu.parse_rasanlu(
                    opsdroid, message, opsdroid.config['parsers'][0])
                self.assertEqual(mock_skill, skills[0]["skill"])

            await opsdroid.run_skill(
                skills[0]["skill"], skills[0]["config"], message)
            self.assertTrue(skills[0]["skill"].called)

    async def test_parse_rasanlu_failure(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            match_rasanlu('get_weather')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("how's the weather outside", "user",
                              "default", mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') as mocked_call_rasanlu:
                mocked_call_rasanlu.return_value = "unauthorized"
                skills = await rasanlu.parse_rasanlu(
                    opsdroid, message, opsdroid.config['parsers'][0])
                self.assertFalse(skills)

    async def test_parse_rasanlu_low_score(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            match_rasanlu('get_weather')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("how's the weather outside", "user",
                              "default", mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') as mocked_call_rasanlu:
                mocked_call_rasanlu.return_value = {
                    "entities": [
                        {
                            "end": 32,
                            "entity": "state",
                            "extractor": "ner_crf",
                            "start": 25,
                            "value": "running"
                        }
                    ],
                    "intent": {
                        "confidence": 0.1745766766665303,
                        "name": "get_weather"
                    },
                    "intent_ranking": [
                        {
                            "confidence": 0.1745766766665303,
                            "name": "get_weather"
                        },
                        {
                            "confidence": 0.42542332333346977,
                            "name": "other_weather"
                        }
                    ],
                    "text": "how's the weather outside"
                }
                await rasanlu.parse_rasanlu(opsdroid, message,
                                            opsdroid.config['parsers'][0])

            self.assertFalse(mock_skill.called)

    async def test_parse_rasanlu_no_entity(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'rasanlu', 'access-token': 'test'}
            ]
            mock_skill = amock.CoroutineMock()
            match_rasanlu('get_weather')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("hi", "user",
                              "default", mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') as mocked_call_rasanlu:
                mocked_call_rasanlu.return_value = {
                    "entities": [],
                    "intent": None,
                    "intent_ranking": [],
                    "text": "hi"
                }
                await rasanlu.parse_rasanlu(opsdroid, message,
                                            opsdroid.config['parsers'][0])

            self.assertFalse(mock_skill.called)

    async def test_parse_rasanlu_no_intent(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            match_rasanlu('get_weather')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("how's the weather outside", "user",
                              "default", mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') as mocked_call_rasanlu:
                mocked_call_rasanlu.return_value = {
                    "entities": [],
                    "intent": None,
                    "intent_ranking": [],
                    "text": "hi"
                }
                await rasanlu.parse_rasanlu(opsdroid, message,
                                            opsdroid.config['parsers'][0])

            self.assertFalse(mock_skill.called)

    async def test_parse_rasanlu_raise_ClientOSError(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            match_rasanlu('get_weather')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("how's the weather outside", "user",
                              "default", mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') as mocked_call:
                mocked_call.side_effect = ClientOSError()
                await rasanlu.parse_rasanlu(opsdroid, message,
                                            opsdroid.config['parsers'][0])

            self.assertFalse(mock_skill.called)
            self.assertTrue(mocked_call.called)

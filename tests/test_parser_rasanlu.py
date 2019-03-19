import asyncio
import asynctest
import asynctest.mock as amock

import aiohttp
from aiohttp import ClientOSError

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_rasanlu
from opsdroid.events import Message
from opsdroid.parsers import rasanlu
from opsdroid.connector import Connector


class TestParserRasaNLU(asynctest.TestCase):
    """Test the opsdroid Rasa NLU parser."""

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

    async def test_call_rasanlu(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        message = Message("how's the weather outside", "user", "default",
                          mock_connector)
        config = {'name': 'rasanlu',
                  'access-token': 'test',
                  'min-score': 0.3,
                  'token': '12345'}
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
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            await rasanlu.call_rasanlu(message.text, config)
            self.assertTrue(patched_request.called)

    async def test_call_rasanlu_bad_response(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        message = Message("how's the weather outside", "user", "default",
                          mock_connector)
        config = {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
        result = amock.Mock()
        result.status = 403
        result.text = amock.CoroutineMock()
        result.text.return_value = "unauthorized"
        with amock.patch('aiohttp.ClientSession.post') as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            response = await rasanlu.call_rasanlu(message.text, config)
            self.assertTrue(patched_request.called)
            self.assertEqual(response, result.text.return_value)

    async def test_call_rasanlu_raises(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        message = Message("how's the weather outside", "user", "default",
                          mock_connector)
        config = {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
        result = amock.Mock()
        result.status = 403
        result.text = amock.CoroutineMock()
        result.text.return_value = "unauthorized"
        with amock.patch('aiohttp.ClientSession.post') as patched_request:
            patched_request.side_effect = \
                aiohttp.client_exceptions.ClientConnectorError(
                    'key', amock.Mock())
            self.assertEqual(None,
                             await rasanlu.call_rasanlu(message.text, config))

    async def test_parse_rasanlu(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
            ]
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_rasanlu('get_weather')(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message("how's the weather outside", "user", "default",
                              mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') \
                    as mocked_call_rasanlu:
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
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])
                self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_rasanlu_raises(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
            ]
            mock_skill = await self.getRaisingMockSkill()
            mock_skill.config = {
                "name": "mocked-skill"
            }
            opsdroid.skills.append(match_rasanlu('get_weather')(mock_skill))

            mock_connector = amock.MagicMock()
            mock_connector.send = amock.CoroutineMock()
            message = Message("how's the weather outside", "user", "default",
                              mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') \
                    as mocked_call_rasanlu:
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
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])
                self.assertEqual(mock_skill, skills[0]["skill"])

            await opsdroid.run_skill(
                skills[0]["skill"], skills[0]["config"], message
            )
            self.assertLogs('_LOGGER', 'exception')

    async def test_parse_rasanlu_failure(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            match_rasanlu('get_weather')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("how's the weather outside", "user", "default",
                              mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') \
                    as mocked_call_rasanlu:
                mocked_call_rasanlu.return_value = "unauthorized"
                skills = await rasanlu.parse_rasanlu(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])
                self.assertFalse(skills)

    async def test_parse_rasanlu_low_score(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'rasanlu', 'access-token': 'test', 'min-score': 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            match_rasanlu('get_weather')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("how's the weather outside", "user", "default",
                              mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') \
                    as mocked_call_rasanlu:
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
                await rasanlu.parse_rasanlu(opsdroid, opsdroid.skills, message,
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
            message = Message("hi", "user", "default",
                              mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') \
                    as mocked_call_rasanlu:
                mocked_call_rasanlu.return_value = {
                    "entities": [],
                    "intent": None,
                    "intent_ranking": [],
                    "text": "hi"
                }
                await rasanlu.parse_rasanlu(opsdroid, opsdroid.skills, message,
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
            message = Message("how's the weather outside", "user", "default",
                              mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') \
                    as mocked_call_rasanlu:
                mocked_call_rasanlu.return_value = {
                    "entities": [],
                    "intent": None,
                    "intent_ranking": [],
                    "text": "hi"
                }
                await rasanlu.parse_rasanlu(opsdroid, opsdroid.skills, message,
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
            message = Message("how's the weather outside", "user", "default",
                              mock_connector)

            with amock.patch.object(rasanlu, 'call_rasanlu') as mocked_call:
                mocked_call.side_effect = ClientOSError()
                await rasanlu.parse_rasanlu(opsdroid, opsdroid.skills, message,
                                            opsdroid.config['parsers'][0])

            self.assertFalse(mock_skill.called)
            self.assertTrue(mocked_call.called)

    async def test__get_all_intents(self):
        skills = [
            await self.getMockSkill(),
            await self.getMockSkill(),
            await self.getMockSkill()
        ]
        skills[0].matchers = [{"intents": "Hello"}]
        skills[1].matchers = [{"intents": None}]
        skills[2].matchers = [{"intents": "World"}]
        intents = await rasanlu._get_all_intents(skills)
        self.assertEqual(type(intents), type(b""))
        self.assertEqual(intents, b"Hello\n\nWorld")

    async def test__get_all_intents_fails(self):
        skills = []
        intents = await rasanlu._get_all_intents(skills)
        self.assertEqual(intents, None)

    async def test__get_intents_fingerprint(self):
        fingerprint = await rasanlu._get_intents_fingerprint(b"")
        self.assertEqual(fingerprint,
                         'e3b0c44298fc1c149afbf4c8996fb924' +
                         '27ae41e4649b934ca495991b7852b855')

        fingerprint = await rasanlu._get_intents_fingerprint(b"Hello World")
        self.assertEqual(fingerprint,
                         'a591a6d40bf420404a011733cfb7b190' +
                         'd62c65bf0bcda32b57b277d9ad9f146e')

        fingerprint = await rasanlu._get_intents_fingerprint(b"Hello\n\nWorld")
        self.assertEqual(fingerprint,
                         '286346b7b2f097fc1c8d8c0436c5e3b1' +
                         'b661768a549f7585a3bda9cc7af2b079')

    async def test__build_training_url(self):
        config = {}
        with self.assertRaises(KeyError):
            await rasanlu._build_training_url(config)

        config = {
            "model": "helloworld"
        }
        url = await rasanlu._build_training_url(config)
        self.assertTrue("helloworld" in url)

        config = {
            "model": "helloworld",
            "token": "abc123"
        }
        url = await rasanlu._build_training_url(config)
        self.assertTrue("&token=abc123" in url)

        config = {
            "url": "http://example.com",
            "project": "myproject",
            "model": "helloworld"
        }
        url = await rasanlu._build_training_url(config)
        self.assertTrue("http://example.com" in url)
        self.assertTrue("myproject" in url)
        self.assertTrue("helloworld" in url)

    async def test__build_status_url(self):
        config = {
            "url": "http://example.com"
        }
        url = await rasanlu._build_status_url(config)
        self.assertTrue("http://example.com" in url)

    async def test__init_model(self):
        with amock.patch.object(rasanlu, 'call_rasanlu') as mocked_call:
            mocked_call.return_value = {"data": "Some data"}
            self.assertEqual(await rasanlu._init_model({}), True)

            mocked_call.return_value = None
            self.assertEqual(await rasanlu._init_model({}), False)

    async def test__get_existing_models(self):
        result = amock.Mock()
        result.status = 200
        result.json = amock.CoroutineMock()
        result.json.return_value = {
            "available_projects": {
                "default": {
                    "available_models": [
                        "fallback"
                    ],
                    "status": "ready"
                },
                "opsdroid": {
                    "available_models": [
                        "hello",
                        "world"
                    ],
                    "status": "ready"
                }
            }
        }
        with amock.patch('aiohttp.ClientSession.get') as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            models = await rasanlu._get_existing_models(
                {"project": "opsdroid"})
            self.assertEqual(models, ["hello", "world"])

    async def test__get_existing_models_exception(self):

        with amock.patch('aiohttp.ClientSession.get') as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.side_effect = ClientOSError()
            models = await rasanlu._get_existing_models(
                {"project": "opsdroid"})
            self.assertRaises(ClientOSError)
            self.assertEqual(models, [])

    async def test__get_existing_models_fails(self):
        result = amock.Mock()
        result.status = 404
        result.json = amock.CoroutineMock()
        result.json.return_value = {}
        with amock.patch('aiohttp.ClientSession.get') as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            models = await rasanlu._get_existing_models({})
            self.assertEqual(models, [])

    async def test_train_rasanlu(self):
        result = amock.Mock()
        result.status = 404
        result.text = amock.CoroutineMock()
        result.json = amock.CoroutineMock()
        result.json.return_value = {
            "info": "new model trained: abc123"
        }

        with amock.patch('aiohttp.ClientSession.post') as patched_request, \
            amock.patch.object(rasanlu, '_get_all_intents') as mock_gai, \
            amock.patch.object(rasanlu, '_init_model') as mock_im, \
            amock.patch.object(rasanlu, '_build_training_url') as mock_btu, \
            amock.patch.object(rasanlu,
                               '_get_existing_models') as mock_gem, \
            amock.patch.object(rasanlu,
                               '_get_intents_fingerprint') as mock_gif:

            mock_gai.return_value = None
            self.assertEqual(await rasanlu.train_rasanlu({}, {}), False)

            mock_gai.return_value = "Hello World"
            mock_gem.return_value = ["abc123"]
            mock_gif.return_value = "abc123"
            self.assertEqual(await rasanlu.train_rasanlu({}, {}), True)
            self.assertTrue(mock_im.called)
            self.assertFalse(mock_btu.called)

            mock_gem.return_value = []
            mock_btu.return_value = "http://example.com"
            patched_request.side_effect = \
                aiohttp.client_exceptions.ClientConnectorError(
                    'key', amock.Mock())
            self.assertEqual(await rasanlu.train_rasanlu({}, {}), False)

            patched_request.side_effect = None
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            self.assertEqual(await rasanlu.train_rasanlu({}, {}), False)

            result.status = 200
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            self.assertEqual(await rasanlu.train_rasanlu({}, {}), True)

            result.json.return_value = {"info": "error"}
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            self.assertEqual(await rasanlu.train_rasanlu({}, {}), False)

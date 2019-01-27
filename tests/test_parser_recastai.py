import asyncio
import asynctest
import asynctest.mock as amock

from aiohttp import ClientOSError

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_recastai
from opsdroid.events import Message
from opsdroid.parsers import recastai
from opsdroid.connector import Connector


class TestParserRecastAi(asynctest.TestCase):
    """Test the opsdroid recastai parser."""

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

    async def test_call_recastai(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        message = Message("user", "default", mock_connector, "Hello")
        config = {'name': 'recastai', 'access-token': 'test'}
        result = amock.Mock()
        result.json = amock.CoroutineMock()
        result.json.return_value = {
            'results':
                {
                    "uuid": "f482bddd-a9d7-41ae-aae3-6e64ad3f02dc",
                    "source": "hello",
                    "intents": [
                        {
                            "slug": "greetings",
                            "confidence": 0.99
                        }
                    ],
                    "act": "assert",
                    "type": None,
                    "sentiment": "vpositive",
                    "entities": {},
                    "language": "en",
                    "processing_language": "en",
                    "version": "2.10.1",
                    "timestamp": "2017-11-15T07:41:48.935990+00:00",
                    "status": 200
                }
        }

        with amock.patch('aiohttp.ClientSession.post') as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            await recastai.call_recastai(message, config)
            self.assertTrue(patched_request.called)

    async def test_parse_recastai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                {'name': 'recastai', 'access-token': "test"}
            ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {
                "name": "greetings"
            }
            opsdroid.skills.append(match_recastai('greetings')(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message("user", "default", mock_connector, "Hello")

            with amock.patch.object(recastai, 'call_recastai') as \
                    mocked_call_recastai:
                mocked_call_recastai.return_value = {
                    'results':
                        {
                            "uuid": "f482bddd-a9d7-41ae-aae3-6e64ad3f02dc",
                            "source": "hello",
                            "intents": [
                                {
                                    "slug": "greetings",
                                    "confidence": 0.99
                                }
                            ],
                            "act": "assert",
                            "type": None,
                            "sentiment": "vpositive",
                            "entities": {},
                            "language": "en",
                            "processing_language": "en",
                            "version": "2.10.1",
                            "timestamp": "2017-11-15T07:41:48.935990+00:00",
                            "status": 200
                        }
                }
                skills = await recastai.parse_recastai(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])
                self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_recastai_raises(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {'name': 'recastai', 'access-token': "test"}
                ]
            mock_skill = await self.getRaisingMockSkill()
            mock_skill.config = {
                "name": "mocked-skill"
            }
            opsdroid.skills.append(match_recastai('greetings')(mock_skill))

            mock_connector = amock.MagicMock()
            mock_connector.respond = amock.CoroutineMock()
            message = Message("user", "default", mock_connector, "Hello")

            with amock.patch.object(recastai, 'call_recastai') as \
                    mocked_call_recastai:
                mocked_call_recastai.return_value = {
                    'results':
                        {
                            "uuid": "f482bddd-a9d7-41ae-aae3-6e64ad3f02dc",
                            "source": "hello",
                            "intents": [
                                {
                                    "slug": "greetings",
                                    "confidence": 0.99
                                }
                            ],
                            "act": "assert",
                            "type": None,
                            "sentiment": "vpositive",
                            "entities": {},
                            "language": "en",
                            "processing_language": "en",
                            "version": "2.10.1",
                            "timestamp": "2017-11-15T07:41:48.935990+00:00",
                            "status": 200
                        }
                }

                skills = await recastai.parse_recastai(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])
                self.assertEqual(mock_skill, skills[0]["skill"])

            await opsdroid.run_skill(
                skills[0]["skill"], skills[0]["config"], message)
            self.assertLogs('_LOGGER', 'exception')

    async def test_parse_recastai_failure(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {'name': 'recastai', 'access-token': "test"}
                ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {
                "name": "greetings"
            }
            opsdroid.skills.append(match_recastai('greetings')(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message("user", "default", mock_connector, "")

            with amock.patch.object(recastai, 'call_recastai') as \
                    mocked_call_recastai:
                mocked_call_recastai.return_value = {
                    'results': None,
                    'message': 'Text is empty'
                }
                skills = await recastai.parse_recastai(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])
                self.assertFalse(skills)

    async def test_parse_recastai_no_intent(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {'name': 'recastai', 'access-token': "test"}
                ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {
                "name": "greetings"
            }
            opsdroid.skills.append(match_recastai('greetings')(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                "user",
                "default",
                mock_connector,
                "kdjiruetosakdg")

            with amock.patch.object(recastai, 'call_recastai') as \
                    mocked_call_recastai:
                mocked_call_recastai.return_value = {
                    'results':
                        {
                            'uuid': 'e4b365be-815b-4e40-99c3-7a25583b4892',
                            'source': 'kdjiruetosakdg',
                            'intents': [],
                            'act': 'assert',
                            'type': None,
                            'sentiment': 'neutral',
                            'entities': {},
                            'language': 'en',
                            'processing_language': 'en',
                            'version': '2.10.1',
                            'timestamp': '2017-11-15T07:32:42.641604+00:00',
                            'status': 200}}

                skills = await recastai.parse_recastai(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])
                self.assertLogs('_LOGGER', 'error')
                self.assertFalse(skills)

    async def test_parse_recastai_low_score(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {
                        'name': 'recastai',
                        'access-token': "test",
                        "min-score": 1.0
                    }
                ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {
                "name": "greetings"
            }
            opsdroid.skills.append(match_recastai('intent')(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message("user", "default", mock_connector, "Hello")

            with amock.patch.object(recastai, 'call_recastai') as \
                    mocked_call_recastai:
                mocked_call_recastai.return_value = {
                    'results':
                        {
                            "uuid": "f482bddd-a9d7-41ae-aae3-6e64ad3f02dc",
                            "source": "hello",
                            "intents": [
                                {
                                    "slug": "greetings",
                                    "confidence": 0.99
                                }
                            ],
                            "act": "assert",
                            "type": None,
                            "sentiment": "vpositive",
                            "entities": {},
                            "language": "en",
                            "processing_language": "en",
                            "version": "2.10.1",
                            "timestamp": "2017-11-15T07:41:48.935990+00:00",
                            "status": 200
                        }
                }
                await recastai.parse_recastai(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])

    async def test_parse_recastai_raise_ClientOSError(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {
                        'name': 'recastai',
                        'access-token': "test",
                    }
                ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {
                "name": "greetings"
            }
            opsdroid.skills.append(match_recastai('greetings')(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message("user", "default", mock_connector, "Hello")

            with amock.patch.object(recastai, 'call_recastai') \
                    as mocked_call:
                mocked_call.side_effect = ClientOSError()
                await recastai.parse_recastai(
                    opsdroid, opsdroid.skills, message, opsdroid.config['parsers'][0])

            self.assertTrue(mocked_call.called)

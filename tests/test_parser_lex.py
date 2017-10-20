
import asynctest
import asynctest.mock as amock

from aiohttp import helpers

from opsdroid.core import OpsDroid
from opsdroid.matchers import match_lex_intent
from opsdroid.message import Message
from opsdroid.parsers import lex
from opsdroid.connector import Connector


class TestParserLex(asynctest.TestCase):
    """Test the opsdroid Lex parser."""

    async def test_call_lex(self):
        mock_connector = Connector({})
        message = Message("Hello world", "user", "default", mock_connector)
        config = {
            'name': 'lex',
            'region': 'test',
            'access_id': 'test',
            'access_secret': 'test',
            'lex_bot': 'test',
            'lex_alias': 'test',
            'lex_user': 'test'
        }
        await lex.call_lex(message, config)
        result = amock.Mock()
        with amock.patch('aiohttp.ClientSession.post') as patched_request:
            patched_request.return_value = helpers.create_future(self.loop)
            patched_request.return_value.set_result(result)
            await lex.call_lex(message, config)
            self.assertTrue(patched_request.called)


    async def test_parse_lex(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {
                        'name': 'lex',
                        'region': 'test',
                        'access_id': 'test',
                        'access_secret': 'test',
                        'lex_bot': 'test',
                        'lex_alias': 'test',
                        'lex_user': 'test'
                    }
                ]
            mock_skill = amock.CoroutineMock()
            match_lex_intent('myintent')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(lex, 'call_lex') as mocked_call_lex:
                mocked_call_lex.return_value = {
                        "result": {
                            "intent": "myintent",
                            "score": 0.7
                        },
                        "status": {
                            "code": 200,
                            "errorType": "success"
                        }
                    }
                await lex.parse_lex(opsdroid, message,
                                    opsdroid.config['parsers'][0])

            self.assertTrue(mock_skill.called)

    async def test_parse_lex_raises(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {
                        'name': 'lex',
                        'region': 'test',
                        'access_id': 'test',
                        'access_secret': 'test',
                        'lex_bot': 'test',
                        'lex_alias': 'test',
                        'lex_user': 'test'
                    }
                ]
            mock_skill = amock.CoroutineMock()
            mock_skill.side_effect = Exception()
            match_lex_intent('myintent')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(lex, 'call_lex') as mocked_call_lex:
                mocked_call_lex.return_value = {
                        "result": {
                            "intent": "myintent",
                            "score": 0.7
                        },
                        "status": {
                            "code": 200,
                            "errorType": "success"
                        }
                    }
                await lex.parse_lex(opsdroid, message,
                                    opsdroid.config['parsers'][0])

            self.assertTrue(mock_skill.called)

    async def test_parse_lex_failure(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {
                        'name': 'lex',
                        'region': 'test',
                        'access_id': 'test',
                        'access_secret': 'test',
                        'lex_bot': 'test',
                        'lex_alias': 'test',
                        'lex_user': 'test'
                    }
                ]
            mock_skill = amock.CoroutineMock()
            match_lex_intent('myintent')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(lex, 'call_lex') as mocked_call_lex:
                mocked_call_lex.return_value = {
                        "result": {
                            "intent": "myintent",
                            "score": 0.7
                        },
                        "status": {
                            "code": 404,
                            "errorType": "not found"
                        }
                    }
                await lex.parse_lex(opsdroid, message,
                                    opsdroid.config['parsers'][0])

            self.assertFalse(mock_skill.called)

    async def test_parse_lex_low_score(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = [
                    {
                        'name': 'lex',
                        'region': 'test',
                        'access_id': 'test',
                        'access_secret': 'test',
                        'lex_bot': 'test',
                        'lex_alias': 'test',
                        'lex_user': 'test',
                        'min-score': 0.8
                    }
                ]
            mock_skill = amock.CoroutineMock()
            match_lex_intent('myintent')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(lex, 'call_lex') as mocked_call_lex:
                mocked_call_lex.return_value = {
                        "result": {
                            "intent": "myintent",
                            "score": 0.7
                        },
                        "status": {
                            "code": 200,
                            "errorType": "success"
                        }
                    }
                await lex.parse_lex(opsdroid, message,
                                    opsdroid.config['parsers'][0])

            self.assertFalse(mock_skill.called)

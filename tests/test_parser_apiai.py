
import asynctest
import asynctest.mock as amock

from aiohttp import helpers

from opsdroid.core import OpsDroid
from opsdroid.skills import match_apiai_action
from opsdroid.message import Message
from opsdroid.parsers import apiai
from opsdroid.connector import Connector


class TestParserApiai(asynctest.TestCase):
    """Test the opsdroid api.ai parser."""

    async def test_call_apiai(self):
        mock_connector = Connector({})
        message = Message("Hello world", "user", "default", mock_connector)
        config = {'access-token': 'test'}
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
            patched_request.return_value = helpers.create_future(self.loop)
            patched_request.return_value.set_result(result)
            await apiai.call_apiai(message, config)
            self.assertTrue(patched_request.called)

    async def test_parse_apiai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = {
                    'apiai': {'access-token': "test"}
                }
            mock_skill = amock.CoroutineMock()
            match_apiai_action('myaction')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(apiai, 'call_apiai') as mocked_call_apiai:
                mocked_call_apiai.return_value = {
                        "result": {
                            "action": "myaction",
                            "score": 0.7
                        },
                        "status": {
                            "code": 200,
                            "errorType": "success"
                        }
                    }
                await apiai.parse_apiai(opsdroid, message)

            self.assertTrue(mock_skill.called)

    async def test_parse_apiai_raises(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = {
                    'apiai': {'access-token': "test"}
                }
            mock_skill = amock.CoroutineMock()
            mock_skill.side_effect = Exception()
            match_apiai_action('myaction')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(apiai, 'call_apiai') as mocked_call_apiai:
                mocked_call_apiai.return_value = {
                        "result": {
                            "action": "myaction",
                            "score": 0.7
                        },
                        "status": {
                            "code": 200,
                            "errorType": "success"
                        }
                    }
                await apiai.parse_apiai(opsdroid, message)

            self.assertTrue(mock_skill.called)

    async def test_parse_apiai_failure(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = {
                    'apiai': {'access-token': "test"}
                }
            mock_skill = amock.CoroutineMock()
            match_apiai_action('myaction')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(apiai, 'call_apiai') as mocked_call_apiai:
                mocked_call_apiai.return_value = {
                        "result": {
                            "action": "myaction",
                            "score": 0.7
                        },
                        "status": {
                            "code": 404,
                            "errorType": "not found"
                        }
                    }
                await apiai.parse_apiai(opsdroid, message)

            self.assertFalse(mock_skill.called)

    async def test_parse_apiai_low_score(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = {
                    'apiai': {'access-token': "test", "min-score": 0.8}
                }
            mock_skill = amock.CoroutineMock()
            match_apiai_action('myaction')(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("Hello world", "user", "default", mock_connector)

            with amock.patch.object(apiai, 'call_apiai') as mocked_call_apiai:
                mocked_call_apiai.return_value = {
                        "result": {
                            "action": "myaction",
                            "score": 0.7
                        },
                        "status": {
                            "code": 200,
                            "errorType": "success"
                        }
                    }
                await apiai.parse_apiai(opsdroid, message)

            self.assertFalse(mock_skill.called)

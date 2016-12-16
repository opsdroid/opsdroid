
import asynctest
import asynctest.mock as amock

from opsdroid.core import OpsDroid
from opsdroid.skills import match_apiai
from opsdroid.message import Message
from opsdroid.parsers import apiai


class TestParserApiai(asynctest.TestCase):
    """Test the opsdroid api.ai parser."""

    async def test_parse_apiai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config['parsers'] = {
                    'apiai': {'access-token': "test"}
                }
            mock_skill = amock.CoroutineMock()
            match_apiai('myaction')(mock_skill)

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
            match_apiai('myaction')(mock_skill)

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
            match_apiai('myaction')(mock_skill)

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

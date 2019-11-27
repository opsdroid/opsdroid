import os
import asyncio
import asynctest
import asynctest.mock as amock

from types import SimpleNamespace

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_dialogflow_action
from opsdroid.events import Message
from opsdroid.parsers import dialogflow
from opsdroid.connector import Connector


class NestedNamespace(SimpleNamespace):
    def __init__(self, dictionary, **kwargs):
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, NestedNamespace(value))
            else:
                self.__setattr__(key, value)


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
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/test.json"
        config = {"name": "dialogflow", "project-id": "test"}
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        message = Message(
            text="Hello", user="user", target="default", connector=mock_connector
        )
        result = amock.Mock()
        result.json = amock.CoroutineMock()
        result.json.return_value = {
            "query_result": {
                "query_text": "what is up",
                "action": "smalltalk.greetings.whatsup",
                "parameters": {},
                "all_required_params_present": True,
                "fulfillment_text": "Not much. What's new with you?",
                "fulfillment_messages": {
                    "text": {"text": "Not much. What's new with you?"}
                },
                "intent": {},
                "intent_detection_confidence": 1.0,
                "language_code": "en",
            }
        }
        with amock.patch("dialogflow.SessionsClient") as patched_request, amock.patch(
            "dialogflow.types.TextInput"
        ) as mocked_input, amock.patch(
            "dialogflow.types.QueryInput"
        ) as mocked_response:
            patched_request.session_path.return_value = (
                "projects/test/agent/sessions/opsdroid"
            )
            mocked_input.return_value = 'text: "hi"'

            mocked_response.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)

            await dialogflow.call_dialogflow(message, opsdroid, config)
            self.assertTrue(patched_request.called)

    async def test_call_dialogflow_failure(self):
        config = {"name": "dialogflow"}
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        message = Message(
            text="Hello", user="user", target="default", connector=mock_connector
        )
        with self.assertRaises(Warning):
            await dialogflow.call_dialogflow(message, opsdroid, config)
            self.assertLogs("_LOGGER", "error")

    async def test_call_dialogflow_import_failure(self):
        with OpsDroid() as opsdroid, amock.patch(
            "dialogflow.SessionsClient"
        ) as patched_request, amock.patch.object(dialogflow, "parse_dialogflow"):
            config = {"name": "dialogflow", "project-id": "test"}
            mock_connector = Connector({}, opsdroid=opsdroid)
            message = Message(
                text="Hello", user="user", target="default", connector=mock_connector
            )
            patched_request.side_effect = ImportError()
            opsdroid.config["parsers"] = [config]

            await dialogflow.call_dialogflow(message, opsdroid, config)

            self.assertLogs("_LOGGER", "error")
            self.assertIn("enabled", opsdroid.config["parsers"][0])
            self.assertEqual(opsdroid.config["parsers"][0]["enabled"], False)

    async def test_parse_dialogflow(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/test.json"
        dialogflow_response = NestedNamespace(
            {
                "query_result": {
                    "query_text": "what is up",
                    "action": "smalltalk.greetings.whatsup",
                    "parameters": {},
                    "all_required_params_present": True,
                    "fulfillment_text": "Not much. What's new with you?",
                    "fulfillment_messages": {
                        "text": {"text": "Not much. What's new with you?"}
                    },
                    "intent": {},
                    "intent_detection_confidence": 1.0,
                    "language_code": "en",
                }
            }
        )

        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "dialogflow", "project-id": "test"}]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(
                match_dialogflow_action("smalltalk.greetings.whatsup")(mock_skill)
            )

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="I want some good French food",
                user="user",
                target="default",
                connector=mock_connector,
            )

            with amock.patch.object(
                dialogflow, "call_dialogflow"
            ) as mocked_call_dialogflow:
                mocked_call_dialogflow.return_value = dialogflow_response

                skills = await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(mock_skill, skills[0]["skill"])
                self.assertLogs("_LOGGERS", "debug")

    async def test_parse_dialogflow_failure(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/test.json"

        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "dialogflow", "project-id": "test"}]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(
                match_dialogflow_action("smalltalk.greetings.whatsup")(mock_skill)
            )

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="Hello", user="user", target="default", connector=mock_connector
            )

            with amock.patch.object(
                dialogflow, "call_dialogflow"
            ) as mocked_call_dialogflow:
                mocked_call_dialogflow.side_effect = Exception()

                skills = await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(skills, None)
                self.assertLogs("_LOGGERS", "debug")

    async def test_parse_dialogflow_low_score(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/test.json"
        dialogflow_response = NestedNamespace(
            {
                "query_result": {
                    "query_text": "what is up",
                    "action": "smalltalk.greetings.whatsup",
                    "parameters": {},
                    "all_required_params_present": True,
                    "fulfillment_text": "Not much. What's new with you?",
                    "fulfillment_messages": {
                        "text": {"text": "Not much. What's new with you?"}
                    },
                    "intent": {},
                    "intent_detection_confidence": 0.3,
                    "language_code": "en",
                }
            }
        )
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "dialogflow", "project-id": "test", "min-score": 0.8}
            ]
            mock_skill = amock.CoroutineMock()
            match_dialogflow_action("myaction")(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="Hello", user="user", target="default", connector=mock_connector
            )

            with amock.patch.object(
                dialogflow, "call_dialogflow"
            ) as mocked_call_dialogflow:
                mocked_call_dialogflow.return_value = dialogflow_response
                await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertFalse(mock_skill.called)
            self.assertLogs("_LOGGERS", "debug")

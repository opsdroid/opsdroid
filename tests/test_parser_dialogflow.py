import asyncio
import asynctest
import asynctest.mock as amock

from aiohttp import ClientOSError

from opsdroid.cli.start import configure_lang
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
        message = Message(
            text="Hello", user="user", target="default", connector=mock_connector
        )
        config = {"name": "dialogflow", "access-token": "test"}
        result = amock.Mock()
        result.json = amock.CoroutineMock()
        result.json.return_value = {
            "result": {"action": "myaction", "score": 0.7},
            "status": {"code": 200, "errorType": "success"},
        }
        with amock.patch("aiohttp.ClientSession.post") as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)

            await dialogflow.call_dialogflow(message, config)
            self.assertTrue(patched_request.called)

    async def test_parse_dialogflow(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "dialogflow", "access-token": "test"}
            ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_dialogflow_action("myaction")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="Hello", user="user", target="default", connector=mock_connector
            )

            with amock.patch.object(
                dialogflow, "call_dialogflow"
            ) as mocked_call_dialogflow:
                mocked_call_dialogflow.return_value = {
                    "result": {"action": "myaction", "score": 0.7},
                    "status": {"code": 200, "errorType": "success"},
                }
                skills = await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_dialogflow_entities(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "dialogflow", "access-token": "test"}
            ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(
                match_dialogflow_action("restaurant.search")(mock_skill)
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
                mocked_call_dialogflow.return_value = {
                    "id": "aab19d9e-3a85-4d44-95ac-2eda162c9663",
                    "timestamp": "2019-05-24T16:44:06.972Z",
                    "lang": "en",
                    "result": {
                        "source": "agent",
                        "resolvedQuery": "I want some good French food",
                        "action": "restaurant.search",
                        "actionIncomplete": False,
                        "parameters": {"Cuisine": "French"},
                        "contexts": [],
                        "metadata": {
                            "intentId": "4e6ce594-6be3-461d-8d5b-418343cfbda6",
                            "webhookUsed": "false",
                            "webhookForSlotFillingUsed": "false",
                            "isFallbackIntent": "false",
                            "intentName": "restaurant.search",
                        },
                        "fulfillment": {
                            "speech": "",
                            "messages": [{"type": 0, "speech": ""}],
                        },
                        "score": 0.8299999833106995,
                    },
                    "status": {"code": 200, "errorType": "success"},
                    "sessionId": "30ad1a2f-e760-d62f-5a21-e8aafc1eaa35",
                }
                [skill] = await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(len(skill["message"].entities.keys()), 1)
                self.assertTrue("Cuisine" in skill["message"].entities.keys())
                self.assertEqual(
                    skill["message"].entities["Cuisine"]["value"], "French"
                )

    async def test_parse_dialogflow_raises(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "dialogflow", "access-token": "test"}
            ]
            mock_skill = await self.getRaisingMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_dialogflow_action("myaction")(mock_skill))

            mock_connector = amock.MagicMock()
            mock_connector.send = amock.CoroutineMock()
            message = Message(
                text="Hello world",
                user="user",
                target="default",
                connector=mock_connector,
            )

            with amock.patch.object(
                dialogflow, "call_dialogflow"
            ) as mocked_call_dialogflow:
                mocked_call_dialogflow.return_value = {
                    "result": {"action": "myaction", "score": 0.7},
                    "status": {"code": 200, "errorType": "success"},
                }
                skills = await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(mock_skill, skills[0]["skill"])

            await opsdroid.run_skill(skills[0]["skill"], skills[0]["config"], message)
            self.assertLogs("_LOGGER", "exception")

    async def test_parse_dialogflow_failure(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "dialogflow", "access-token": "test"}
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
                mocked_call_dialogflow.return_value = {
                    "result": {"action": "myaction", "score": 0.7},
                    "status": {"code": 404, "errorType": "not found"},
                }
                skills = await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertFalse(skills)

    async def test_parse_dialogflow_low_score(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "dialogflow", "access-token": "test", "min-score": 0.8}
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
                mocked_call_dialogflow.return_value = {
                    "result": {"action": "myaction", "score": 0.7},
                    "status": {"code": 200, "errorType": "success"},
                }
                await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertFalse(mock_skill.called)

    async def test_parse_dialogflow_raise_ClientOSError(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "dialogflow", "access-token": "test", "min-score": 0.8}
            ]
            mock_skill = amock.CoroutineMock()
            match_dialogflow_action("myaction")(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="Hello", user="user", target="default", connector=mock_connector
            )

            with amock.patch.object(dialogflow, "call_dialogflow") as mocked_call:
                mocked_call.side_effect = ClientOSError()
                await dialogflow.parse_dialogflow(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertFalse(mock_skill.called)
            self.assertTrue(mocked_call.called)

import asyncio
import asynctest
import asynctest.mock as amock

from aiohttp import ClientOSError

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_luisai_intent
from opsdroid.events import Message
from opsdroid.parsers import luisai
from opsdroid.connector import Connector


class TestParserLuisai(asynctest.TestCase):
    """Test the opsdroid luis.ai parser."""

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

    async def test_call_luisai(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        message = Message(
            text="schedule meeting",
            user="user",
            target="default",
            connector=mock_connector,
        )
        config = {"name": "luisai", "appid": "test", "appkey": "test", "verbose": True}
        result = amock.Mock()
        result.json = amock.CoroutineMock()
        result.json.return_value = {
            "query": "schedule meeting",
            "topScoringIntent": {"intent": "Calendar.Add", "score": 0.900492251},
            "intents": [{"intent": "Calendar.Add", "score": 0.900492251}],
            "entities": [],
        }
        with amock.patch("aiohttp.ClientSession.get") as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            await luisai.call_luisai(message, config)
            self.assertTrue(patched_request.called)

    async def test_parse_luisai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "luisai", "appid": "test", "appkey": "test", "verbose": True}
            ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_luisai_intent("Calendar.Add")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="schedule meeting",
                user="user",
                target="default",
                connector=mock_connector,
            )

            with amock.patch.object(luisai, "call_luisai") as mocked_call_luisai:
                mocked_call_luisai.return_value = {
                    "query": "schedule meeting",
                    "topScoringIntent": {
                        "intent": "Calendar.Add",
                        "score": 0.900492251,
                    },
                    "intents": [{"intent": "Calendar.Add", "score": 0.900492251}],
                    "entities": [],
                }
                skills = await luisai.parse_luisai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_luisai_nointents(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "luisai", "appid": "test", "appkey": "test", "verbose": True}
            ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_luisai_intent("Calendar.Add")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="schedule meeting",
                user="user",
                target="default",
                connector=mock_connector,
            )

            with amock.patch.object(luisai, "call_luisai") as mocked_call_luisai:
                mocked_call_luisai.return_value = {
                    "query": "schedule meeting",
                    "topScoringIntent": {
                        "intent": "Calendar.Add",
                        "score": 0.900492251,
                    },
                    "entities": [],
                }
                skills = await luisai.parse_luisai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertFalse(skills)

    async def test_parse_luisai_raises(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "luisai", "appid": "test", "appkey": "test", "verbose": True}
            ]
            mock_skill = await self.getRaisingMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_luisai_intent("Calendar.Add")(mock_skill))

            mock_connector = amock.MagicMock()
            mock_connector.send = amock.CoroutineMock()
            message = Message(
                text="schedule meeting",
                user="user",
                target="default",
                connector=mock_connector,
            )

            with amock.patch.object(luisai, "call_luisai") as mocked_call_luisai:
                mocked_call_luisai.return_value = {
                    "query": "schedule meeting",
                    "topScoringIntent": {
                        "intent": "Calendar.Add",
                        "score": 0.900492251,
                    },
                    "intents": [{"intent": "Calendar.Add", "score": 0.900492251}],
                    "entities": [],
                }
                skills = await luisai.parse_luisai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(mock_skill, skills[0]["skill"])

            await opsdroid.run_skill(skills[0]["skill"], skills[0]["config"], message)
            self.assertLogs("_LOGGER", "exception")

    async def test_parse_luisai_failure(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "luisai", "appid": "test", "appkey": "test", "verbose": True}
            ]
            mock_skill = amock.CoroutineMock()
            match_luisai_intent("Calendar.Add")(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="schedule meeting",
                user="user",
                target="default",
                connector=mock_connector,
            )

            with amock.patch.object(luisai, "call_luisai") as mocked_call_luisai:
                mocked_call_luisai.return_value = {"statusCode": 401}
                skills = await luisai.parse_luisai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertFalse(skills)

    async def test_parse_luisai_low_score(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {
                    "name": "luisai",
                    "appid": "test",
                    "appkey": "test",
                    "verbose": True,
                    "min-score": 0.95,
                }
            ]
            mock_skill = amock.CoroutineMock()
            match_luisai_intent("Calendar.Add")(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="schedule meeting",
                user="user",
                target="default",
                connector=mock_connector,
            )

            with amock.patch.object(luisai, "call_luisai") as mocked_call_luisai:
                mocked_call_luisai.return_value = {
                    "query": "schedule meeting",
                    "topScoringIntent": {
                        "intent": "Calendar.Add",
                        "score": 0.900492251,
                    },
                    "intents": [{"intent": "Calendar.Add", "score": 0.900492251}],
                    "entities": [],
                }
                await luisai.parse_luisai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertFalse(mock_skill.called)

    async def test_parse_luisai_raise_ClientOSError(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {
                    "name": "luisai",
                    "appid": "test",
                    "appkey": "test",
                    "verbose": True,
                    "min-score": 0.95,
                }
            ]
            mock_skill = amock.CoroutineMock()
            match_luisai_intent("Calendar.Add")(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="schedule meeting",
                user="user",
                target="default",
                connector=mock_connector,
            )

            with amock.patch.object(luisai, "call_luisai") as mocked_call:
                mocked_call.side_effect = ClientOSError()
                await luisai.parse_luisai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertFalse(mock_skill.called)
            self.assertTrue(mocked_call.called)

    async def test_parse_luisai_with_entities(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "luisai", "appid": "test", "appkey": "test", "verbose": True}
            ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "weather"}
            opsdroid.skills.append(match_luisai_intent("weatherLocation")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="whats the weather in london",
                user="user",
                target="default",
                connector=mock_connector,
            )

            with amock.patch.object(luisai, "call_luisai") as mocked_call_luisai:
                mocked_call_luisai.return_value = {
                    "query": "whats the weather in london",
                    "topScoringIntent": {
                        "intent": "weatherLocation",
                        "score": 0.918992,
                    },
                    "intents": [
                        {"intent": "weatherLocation", "score": 0.918992},
                        {"intent": "None", "score": 0.03931402},
                    ],
                    "entities": [
                        {
                            "entity": "london",
                            "type": "builtin.geographyV2.city",
                            "startIndex": 21,
                            "endIndex": 26,
                            "role": "location",
                        }
                    ],
                    "sentimentAnalysis": {"label": "neutral", "score": 0.5},
                }
                [skill] = await luisai.parse_luisai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(len(skill["message"].entities.keys()), 1)
                self.assertTrue("location" in skill["message"].entities.keys())
                self.assertEqual(
                    skill["message"].entities["location"]["value"], "london"
                )

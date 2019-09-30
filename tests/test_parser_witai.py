import asyncio
import asynctest
import asynctest.mock as amock

from aiohttp import ClientOSError

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_witai
from opsdroid.events import Message
from opsdroid.parsers import witai
from opsdroid.connector import Connector


class TestParserWitai(asynctest.TestCase):
    """Test the opsdroid wit.ai parser."""

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

    async def test_call_witai(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        message = Message(
            "how's the weather outside", "user", "default", mock_connector
        )
        config = {"name": "witai", "access-token": "test", "min-score": 0.3}
        result = amock.Mock()
        result.json = amock.CoroutineMock()
        result.json.return_value = {
            "msg_id": "0fI07qSgCwM79NEjs",
            "_text": "how's the weather outside",
            "entities": {
                "intent": [{"confidence": 0.99897986426571, "value": "get_weather"}]
            },
        }
        with amock.patch("aiohttp.ClientSession.get") as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            await witai.call_witai(message, config)
            self.assertTrue(patched_request.called)

    async def test_parse_witai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "witai", "access-token": "test", "min-score": 0.3}
            ]
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_witai("get_weather")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                "how's the weather outside", "user", "default", mock_connector
            )

            with amock.patch.object(witai, "call_witai") as mocked_call_witai:
                mocked_call_witai.return_value = {
                    "msg_id": "0fI07qSgCwM79NEjs",
                    "_text": "how's the weather outside",
                    "entities": {
                        "intent": [
                            {"confidence": 0.99897986426571, "value": "get_weather"}
                        ]
                    },
                }
                skills = await witai.parse_witai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_witai_raises(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "witai", "access-token": "test", "min-score": 0.3}
            ]
            mock_skill = await self.getRaisingMockSkill()
            mock_skill.config = {"name": "mocked-skill"}
            opsdroid.skills.append(match_witai("get_weather")(mock_skill))

            mock_connector = amock.MagicMock()
            mock_connector.send = amock.CoroutineMock()
            message = Message(
                "how's the weather outside", "user", "default", mock_connector
            )

            with amock.patch.object(witai, "call_witai") as mocked_call_witai:
                mocked_call_witai.return_value = {
                    "msg_id": "0fI07qSgCwM79NEjs",
                    "_text": "how's the weather outside",
                    "entities": {
                        "intent": [
                            {"confidence": 0.99897986426571, "value": "get_weather"}
                        ]
                    },
                }
                skills = await witai.parse_witai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(mock_skill, skills[0]["skill"])

            await opsdroid.run_skill(skills[0], skills[0]["skill"].config, message)
            self.assertLogs("_LOGGER", "exception")

    async def test_parse_witai_failure(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "witai", "access-token": "test", "min-score": 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            match_witai("get_weather")(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message(
                "how's the weather outside", "user", "default", mock_connector
            )

            with amock.patch.object(witai, "call_witai") as mocked_call_witai:
                mocked_call_witai.return_value = {
                    "code": "auth",
                    "error": "missing or wrong auth token",
                }
                skills = await witai.parse_witai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertFalse(skills)

    async def test_parse_witai_low_score(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "witai", "access-token": "test", "min-score": 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            match_witai("get_weather")(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message(
                "how's the weather outside", "user", "default", mock_connector
            )

            with amock.patch.object(witai, "call_witai") as mocked_call_witai:
                mocked_call_witai.return_value = {
                    "msg_id": "0fI07qSgCwM79NEjs",
                    "_text": "how's the weather outside",
                    "entities": {
                        "intent": [
                            {"confidence": 0.19897986426571, "value": "get_weather"}
                        ]
                    },
                }
                await witai.parse_witai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertFalse(mock_skill.called)

    async def test_parse_witai_no_entity(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "witai", "access-token": "test"}]
            mock_skill = amock.CoroutineMock()
            match_witai("get_weather")(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message("hi", "user", "default", mock_connector)

            with amock.patch.object(witai, "call_witai") as mocked_call_witai:
                mocked_call_witai.return_value = {
                    "msg_id": "0MDw4dxgcoIyBZeVx",
                    "_text": "hi",
                    "entities": {},
                }
                await witai.parse_witai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertFalse(mock_skill.called)

    async def test_parse_witai_no_intent(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "witai", "access-token": "test", "min-score": 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            match_witai("get_weather")(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message(
                "how's the weather outside", "user", "default", mock_connector
            )

            with amock.patch.object(witai, "call_witai") as mocked_call_witai:
                mocked_call_witai.return_value = {
                    "msg_id": "0fI07qSgCwM79NEjs",
                    "_text": "Book an appointment for today",
                    "entities": {"test": [{"value": "test"}]},
                }
                await witai.parse_witai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertFalse(mock_skill.called)

    async def test_parse_witai_raise_ClientOSError(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "witai", "access-token": "test", "min-score": 0.3}
            ]
            mock_skill = amock.CoroutineMock()
            match_witai("get_weather")(mock_skill)

            mock_connector = amock.CoroutineMock()
            message = Message(
                "how's the weather outside", "user", "default", mock_connector
            )

            with amock.patch.object(witai, "call_witai") as mocked_call:
                mocked_call.side_effect = ClientOSError()
                await witai.parse_witai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertFalse(mock_skill.called)
            self.assertTrue(mocked_call.called)

    async def test_parse_witai_entities(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "witai", "access-token": "test", "min-score": 0.3}
            ]
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_witai("get_weather")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                "what is the weather in london", "user", "default", mock_connector
            )

            with amock.patch.object(witai, "call_witai") as mocked_call_witai:
                mocked_call_witai.return_value = {
                    "msg_id": "0fI07qSgCwM79NEjs",
                    "_text": "what is the weather in london",
                    "entities": {
                        "intent": [
                            {"confidence": 0.99897986426571, "value": "get_weather"}
                        ],
                        "location": [
                            {
                                "confidence": 0.93009,
                                "value": "london",
                                "resolved": {
                                    "values": [
                                        {
                                            "name": "London",
                                            "grain": "locality",
                                            "type": "resolved",
                                            "timezone": "Europe/London",
                                            "coords": {
                                                "lat": 51.508529663086,
                                                "long": -0.12574000656605,
                                            },
                                            "external": {
                                                "geonames": "2643743",
                                                "wikidata": "Q84",
                                                "wikipedia": "London",
                                            },
                                        },
                                        {
                                            "name": "London",
                                            "grain": "locality",
                                            "type": "resolved",
                                            "timezone": "America/New_York",
                                            "coords": {
                                                "lat": 39.886451721191,
                                                "long": -83.448249816895,
                                            },
                                            "external": {
                                                "geonames": "4517009",
                                                "wikidata": "Q1001456",
                                                "wikipedia": "London, Ohio",
                                            },
                                        },
                                        {
                                            "name": "London",
                                            "grain": "locality",
                                            "type": "resolved",
                                            "timezone": "America/Toronto",
                                            "coords": {
                                                "lat": 42.983390808105,
                                                "long": -81.233039855957,
                                            },
                                            "external": {
                                                "geonames": "6058560",
                                                "wikidata": "Q22647924",
                                            },
                                        },
                                    ]
                                },
                            }
                        ],
                    },
                }
                [skill] = await witai.parse_witai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertEqual(len(skill["message"].entities.keys()), 1)
            self.assertTrue("location" in skill["message"].entities.keys())
            self.assertEqual(skill["message"].entities["location"]["value"], "london")

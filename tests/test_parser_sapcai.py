import asyncio
import asynctest
import asynctest.mock as amock

from aiohttp import ClientOSError

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_sapcai
from opsdroid.events import Message
from opsdroid.parsers import sapcai
from opsdroid.connector import Connector


class TestParserRecastAi(asynctest.TestCase):
    """Test the opsdroid sapcai parser."""

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

    async def test_call_sapcai(self):
        opsdroid = amock.CoroutineMock()
        mock_connector = Connector({}, opsdroid=opsdroid)
        message = Message(
            text="Hello", user="user", target="default", connector=mock_connector
        )
        config = {"name": "recastai", "token": "test"}
        result = amock.Mock()
        result.json = amock.CoroutineMock()
        result.json.return_value = {
            "results": {
                "uuid": "f482bddd-a9d7-41ae-aae3-6e64ad3f02dc",
                "source": "hello",
                "intents": [{"slug": "greetings", "confidence": 0.99}],
                "act": "assert",
                "type": None,
                "sentiment": "vpositive",
                "entities": {},
                "language": "en",
                "processing_language": "en",
                "version": "2.10.1",
                "timestamp": "2017-11-15T07:41:48.935990+00:00",
                "status": 200,
            }
        }

        with amock.patch("aiohttp.ClientSession.post") as patched_request:
            patched_request.return_value = asyncio.Future()
            patched_request.return_value.set_result(result)
            await sapcai.call_sapcai(message, config)
            self.assertTrue(patched_request.called)

    async def test_parse_sapcai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "sapcai", "token": "test"}]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_sapcai("greetings")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="Hello", user="user", target="default", connector=mock_connector
            )

            with amock.patch.object(sapcai, "call_sapcai") as mocked_call_sapcai:
                mocked_call_sapcai.return_value = {
                    "results": {
                        "uuid": "f482bddd-a9d7-41ae-aae3-6e64ad3f02dc",
                        "source": "hello",
                        "intents": [{"slug": "greetings", "confidence": 0.99}],
                        "act": "assert",
                        "type": None,
                        "sentiment": "vpositive",
                        "entities": {},
                        "language": "en",
                        "processing_language": "en",
                        "version": "2.10.1",
                        "timestamp": "2017-11-15T07:41:48.935990+00:00",
                        "status": 200,
                    }
                }
                skills = await sapcai.parse_sapcai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_sapcai_raises(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "sapcai", "token": "test"}]
            mock_skill = await self.getRaisingMockSkill()
            mock_skill.config = {"name": "mocked-skill"}
            opsdroid.skills.append(match_sapcai("greetings")(mock_skill))

            mock_connector = amock.MagicMock()
            mock_connector.send = amock.CoroutineMock()
            message = Message(
                text="Hello", user="user", target="default", connector=mock_connector
            )

            with amock.patch.object(sapcai, "call_sapcai") as mocked_call_sapcai:
                mocked_call_sapcai.return_value = {
                    "results": {
                        "uuid": "f482bddd-a9d7-41ae-aae3-6e64ad3f02dc",
                        "source": "hello",
                        "intents": [{"slug": "greetings", "confidence": 0.99}],
                        "act": "assert",
                        "type": None,
                        "sentiment": "vpositive",
                        "entities": {},
                        "language": "en",
                        "processing_language": "en",
                        "version": "2.10.1",
                        "timestamp": "2017-11-15T07:41:48.935990+00:00",
                        "status": 200,
                    }
                }

                skills = await sapcai.parse_sapcai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertEqual(mock_skill, skills[0]["skill"])

            await opsdroid.run_skill(skills[0]["skill"], skills[0]["config"], message)
            self.assertLogs("_LOGGER", "exception")

    async def test_parse_sapcai_failure(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "sapcai", "token": "test"}]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_sapcai("greetings")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="", user="user", target="default", connector=mock_connector
            )

            with amock.patch.object(sapcai, "call_sapcai") as mocked_call_sapcai:
                mocked_call_sapcai.return_value = {
                    "results": None,
                    "message": "Text is empty",
                }
                skills = await sapcai.parse_sapcai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertFalse(skills)

    async def test_parse_sapcai_no_intent(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "sapcai", "token": "test"}]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_sapcai("greetings")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="kdjiruetosakdg",
                user="user",
                target="default",
                connector=mock_connector,
            )

            with amock.patch.object(sapcai, "call_sapcai") as mocked_call_sapcai:
                mocked_call_sapcai.return_value = {
                    "results": {
                        "uuid": "e4b365be-815b-4e40-99c3-7a25583b4892",
                        "source": "kdjiruetosakdg",
                        "intents": [],
                        "act": "assert",
                        "type": None,
                        "sentiment": "neutral",
                        "entities": {},
                        "language": "en",
                        "processing_language": "en",
                        "version": "2.10.1",
                        "timestamp": "2017-11-15T07:32:42.641604+00:00",
                        "status": 200,
                    }
                }

                skills = await sapcai.parse_sapcai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )
                self.assertLogs("_LOGGER", "error")
                self.assertFalse(skills)

    async def test_parse_sapcai_low_score(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [
                {"name": "sapcai", "token": "test", "min-score": 1.0}
            ]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_sapcai("intent")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="Hello", user="user", target="default", connector=mock_connector
            )

            with amock.patch.object(sapcai, "call_sapcai") as mocked_call_sapcai:
                mocked_call_sapcai.return_value = {
                    "results": {
                        "uuid": "f482bddd-a9d7-41ae-aae3-6e64ad3f02dc",
                        "source": "hello",
                        "intents": [{"slug": "greetings", "confidence": 0.99}],
                        "act": "assert",
                        "type": None,
                        "sentiment": "vpositive",
                        "entities": {},
                        "language": "en",
                        "processing_language": "en",
                        "version": "2.10.1",
                        "timestamp": "2017-11-15T07:41:48.935990+00:00",
                        "status": 200,
                    }
                }
                await sapcai.parse_sapcai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

    async def test_parse_sapcai_raise_ClientOSError(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "sapcai", "token": "test"}]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_sapcai("greetings")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="Hello", user="user", target="default", connector=mock_connector
            )

            with amock.patch.object(sapcai, "call_sapcai") as mocked_call:
                mocked_call.side_effect = ClientOSError()
                await sapcai.parse_sapcai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertTrue(mocked_call.called)

    async def test_parse_sapcai_with_entities(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "sapcai", "token": "test"}]
            mock_skill = await self.getMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_sapcai("weather")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = Message(
                text="whats the weather in london",
                user="user",
                target="default",
                connector=mock_connector,
            )

            with amock.patch.object(sapcai, "call_sapcai") as mocked_call_sapcai:
                mocked_call_sapcai.return_value = {
                    "results": {
                        "uuid": "f058ad85-d089-40e1-a910-a76990d36180",
                        "intents": [
                            {
                                "slug": "weather",
                                "confidence": 0.97,
                                "description": "weather",
                            }
                        ],
                        "entities": {
                            "location": [
                                {
                                    "formatted": "London, UK",
                                    "lat": 51.5073509,
                                    "lng": -0.1277583,
                                    "type": "locality",
                                    "place": "ChIJdd4hrwug2EcRmSrV3Vo6llI",
                                    "raw": "london",
                                    "confidence": 0.99,
                                    "country": "gb",
                                }
                            ]
                        },
                        "language": "en",
                        "processing_language": "en",
                        "version": "1903.6.2",
                        "timestamp": "2019-06-02T12:22:57.216286+00:00",
                        "status": 200,
                        "source": "whats the weather in london",
                        "act": "wh-query",
                        "type": "desc:desc",
                        "sentiment": "neutral",
                    },
                    "message": "Requests rendered with success",
                }

                [skill] = await sapcai.parse_sapcai(
                    opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
                )

            self.assertEqual(len(skill["message"].entities.keys()), 1)
            self.assertTrue("location" in skill["message"].entities.keys())
            self.assertEqual(skill["message"].entities["location"]["value"], "london")

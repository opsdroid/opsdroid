import asynctest
import asynctest.mock as amock

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_mention
from opsdroid.events import Message
from opsdroid.parsers.mention import parse_mention
from opsdroid.connector.matrix import ConnectorMatrix


class TestParserMention(asynctest.TestCase):
    """Test the opsdroid mention parser."""

    @property
    def message_json(self):
        return {
            "content": {
                "body": "Hello Alice!",
                "msgtype": "m.text",
                "format": "org.matrix.custom.html",
                "formatted_body": "Hello <a href='https://matrix.to/#/@alice:example.org'>Alice</a>!",
            },
            "event_id": "$eventid:localhost",
            "origin_server_ts": 1547124373956,
            "sender": "@bob:example.com",
            "type": "m.room.message",
            "unsigned": {"age": 3498},
        }

    async def setup(self):
        configure_lang({})

    async def getMockSkill(self):
        async def mockedskill(config, message):
            pass

        mockedskill.config = {}
        return mockedskill

    async def getRaisingMockSkill(self):
        async def mockedskill(config, message):
            raise Exception()

        mockedskill.config = {}
        return mockedskill

    async def test_parse_mention_decorator_parens(self):
        with OpsDroid() as opsdroid:
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_mention()(mock_skill))
            opsdroid.run_skill = amock.CoroutineMock()

            connector = ConnectorMatrix(
                {
                    "name": "matrix",
                    "rooms": {"main": "#test:localhost"},
                    "mxid": "@alice:example.org",
                    "password": "hello",
                    "homeserver": "http://localhost:8008",
                },
                opsdroid=OpsDroid(),
            )
            opsdroid.connectors.append(connector)

            message = Message(
                text="Hello world",
                user="user",
                target="default",
                connector=connector,
                raw_event=self.message_json,
            )

            await parse_mention(opsdroid, opsdroid.skills, message)
            skills = await opsdroid.get_ranked_skills(opsdroid.skills, message)
            self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_mention_decorate_no_parens(self):
        with OpsDroid() as opsdroid:
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_mention(mock_skill))
            opsdroid.run_skill = amock.CoroutineMock()

            connector = ConnectorMatrix(
                {
                    "name": "matrix",
                    "rooms": {"main": "#test:localhost"},
                    "mxid": "@alice:example.org",
                    "password": "hello",
                    "homeserver": "http://localhost:8008",
                },
                opsdroid=OpsDroid(),
            )
            opsdroid.connectors.append(connector)

            message = Message(
                text="Hello world",
                user="user",
                target="default",
                connector=connector,
                raw_event=self.message_json,
            )

            await parse_mention(opsdroid, opsdroid.skills, message)
            skills = await opsdroid.get_ranked_skills(opsdroid.skills, message)
            self.assertEqual(mock_skill, skills[0]["skill"])

    async def test_parse_mention_raises(self):
        with OpsDroid() as opsdroid:
            mock_skill = await self.getRaisingMockSkill()
            mock_skill.config = {"name": "greetings"}
            opsdroid.skills.append(match_mention()(mock_skill))
            self.assertEqual(len(opsdroid.skills), 1)

            mock_connector = amock.MagicMock()
            mock_connector.send = amock.CoroutineMock()
            message = Message(
                text="Hello world",
                user="user",
                target="default",
                connector=mock_connector,
            )

            await parse_mention(opsdroid, opsdroid.skills, message)
            self.assertLogs("_LOGGER", "exception")

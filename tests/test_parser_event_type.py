import asynctest
import asynctest.mock as amock

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.matchers import match_event
from opsdroid import events
from opsdroid.parsers.event_type import parse_event_type
from opsdroid.constraints import constrain_rooms


class TestParserEvent(asynctest.TestCase):
    """Test the opsdroid event parser."""

    async def setup(self):
        configure_lang({})

    async def getMockSkill(self):
        async def mockedskill(opsdroid, config, message):
            pass

        mockedskill.config = {}
        return mockedskill

    async def test_parse_message(self):
        with OpsDroid() as opsdroid:
            opsdroid.run_skill = amock.CoroutineMock()
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_event(events.Message)(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = events.Message("Hello World", "user", "default", mock_connector)

            await opsdroid.parse(message)
            self.assertTrue(opsdroid.run_skill.called)

    async def test_parse_event_with_args(self):
        with OpsDroid() as opsdroid:
            opsdroid.run_skill = amock.CoroutineMock()
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(
                match_event(events.Message, value="click_me_123")(mock_skill)
            )

            mock_connector = amock.CoroutineMock()
            message1 = events.Message("Hello World", "user", "default", mock_connector)
            message1.update_entity("value", "click_me_123")

            await opsdroid.parse(message1)
            self.assertTrue(opsdroid.run_skill.called)

            opsdroid.run_skill.reset_mock()

            message2 = events.Message("Hello World", "user", "default", mock_connector)
            message2.update_entity("value", "click_me_456")

            await opsdroid.parse(message2)
            self.assertFalse(opsdroid.run_skill.called)

    async def test_parse_event_with_args_list(self):
        with OpsDroid() as opsdroid:
            opsdroid.run_skill = amock.CoroutineMock()
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(
                match_event(events.Message, value=["click_me_123"])(mock_skill)
            )

            mock_connector = amock.CoroutineMock()
            message1 = events.Message("Hello World", "user", "default", mock_connector)
            message1.update_entity("value", ["click_me_123"])

            await opsdroid.parse(message1)
            self.assertTrue(opsdroid.run_skill.called)

    async def test_parse_event_with_constraint(self):
        with OpsDroid() as opsdroid:
            opsdroid.run_skill = amock.CoroutineMock()
            mock_skill = await self.getMockSkill()
            mock_skill = match_event(events.JoinRoom)(mock_skill)
            mock_skill = constrain_rooms(["#general"])(mock_skill)
            opsdroid.skills.append(mock_skill)

            mock_connector = amock.CoroutineMock()
            mock_connector.lookup_target = amock.Mock(return_value="some_room_id")
            message = events.JoinRoom(
                user="user", target="some_room_id", connector=mock_connector
            )

            await opsdroid.parse(message)
            self.assertTrue(opsdroid.run_skill.called)

    async def test_parse_str_event(self):
        with OpsDroid() as opsdroid:
            opsdroid.run_skill = amock.CoroutineMock()
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_event("Message")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = events.Message("Hello World", "user", "default", mock_connector)

            await opsdroid.parse(message)
            self.assertTrue(opsdroid.run_skill.called)

    async def test_parse_invalid_str(self):
        with OpsDroid() as opsdroid:
            mock_skill = await self.getMockSkill()
            opsdroid.skills.append(match_event("Message2")(mock_skill))

            mock_connector = amock.CoroutineMock()
            message = events.Message("Hello World", "user", "default", mock_connector)

            with self.assertRaises(ValueError):
                await parse_event_type(opsdroid, message)

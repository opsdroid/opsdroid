import asynctest
import asynctest.mock as mock

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.events import Message
from opsdroid.matchers import match_regex
from opsdroid import constraints


class TestConstraints(asynctest.TestCase):
    """Test the opsdroid constraint decorators."""

    async def setUp(self):
        configure_lang({})

    async def getMockSkill(self):
        async def mockedskill(opsdroid, config, message):
            pass

        mockedskill.config = {}
        return mockedskill

    async def test_constrain_rooms_constrains(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop = mock.CoroutineMock()
            skill = await self.getMockSkill()
            skill = match_regex(r".*")(skill)
            skill = constraints.constrain_rooms(["#general"])(skill)
            opsdroid.skills.append(skill)

            tasks = await opsdroid.parse(Message("Hello", "user", "#random", None))
            self.assertEqual(len(tasks), 1)  # Just match_always

    async def test_constrain_rooms_skips(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop = mock.CoroutineMock()
            skill = await self.getMockSkill()
            skill = match_regex(r".*")(skill)
            skill = constraints.constrain_rooms(["#general"])(skill)
            opsdroid.skills.append(skill)

            tasks = await opsdroid.parse(Message("Hello", "user", "#general", None))
            self.assertEqual(len(tasks), 2)  # match_always and the skill

    async def test_constrain_rooms_inverted(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop = mock.CoroutineMock()
            skill = await self.getMockSkill()
            skill = match_regex(r".*")(skill)
            skill = constraints.constrain_rooms(["#general"], invert=True)(skill)
            opsdroid.skills.append(skill)

            tasks = await opsdroid.parse(Message("Hello", "user", "#general", None))
            self.assertEqual(len(tasks), 1)  # match_always only

    async def test_constrain_users_constrains(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop = mock.CoroutineMock()
            skill = await self.getMockSkill()
            skill = match_regex(r".*")(skill)
            skill = constraints.constrain_users(["user"])(skill)
            opsdroid.skills.append(skill)

            tasks = await opsdroid.parse(
                Message("Hello", "otheruser", "#general", None)
            )
            self.assertEqual(len(tasks), 1)  # Just match_always

    async def test_constrain_users_skips(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop = mock.CoroutineMock()
            skill = await self.getMockSkill()
            skill = match_regex(r".*")(skill)
            skill = constraints.constrain_users(["user"])(skill)
            opsdroid.skills.append(skill)

            tasks = await opsdroid.parse(Message("Hello", "user", "#general", None))
            self.assertEqual(len(tasks), 2)  # match_always and the skill

    async def test_constrain_users_inverted(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop = mock.CoroutineMock()
            skill = await self.getMockSkill()
            skill = match_regex(r".*")(skill)
            skill = constraints.constrain_users(["user"], invert=True)(skill)
            opsdroid.skills.append(skill)

            tasks = await opsdroid.parse(Message("Hello", "user", "#general", None))
            self.assertEqual(len(tasks), 1)  # match_always only

    async def test_constrain_connectors_constrains(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop = mock.CoroutineMock()
            skill = await self.getMockSkill()
            skill = match_regex(r".*")(skill)
            skill = constraints.constrain_connectors(["slack"])(skill)
            opsdroid.skills.append(skill)
            connector = mock.Mock()
            connector.configure_mock(name="twitter")

            tasks = await opsdroid.parse(Message("Hello", "user", "#random", connector))
            self.assertEqual(len(tasks), 1)  # Just match_always

    async def test_constrain_connectors_skips(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop = mock.CoroutineMock()
            skill = await self.getMockSkill()
            skill = match_regex(r".*")(skill)
            skill = constraints.constrain_connectors(["slack"])(skill)
            opsdroid.skills.append(skill)
            connector = mock.Mock()
            connector.configure_mock(name="slack")

            tasks = await opsdroid.parse(
                Message("Hello", "user", "#general", connector)
            )
            self.assertEqual(len(tasks), 2)  # match_always and the skill

    async def test_constrain_connectors_inverted(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop = mock.CoroutineMock()
            skill = await self.getMockSkill()
            skill = match_regex(r".*")(skill)
            skill = constraints.constrain_connectors(["slack"], invert=True)(skill)
            opsdroid.skills.append(skill)
            connector = mock.Mock()
            connector.configure_mock(name="slack")

            tasks = await opsdroid.parse(
                Message("Hello", "user", "#general", connector)
            )
            self.assertEqual(len(tasks), 1)  # match_always only

    async def test_constraint_can_be_called_after_skip(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop = mock.CoroutineMock()
            skill = await self.getMockSkill()
            skill = match_regex(r".*")(skill)
            skill = constraints.constrain_users(["user"])(skill)
            opsdroid.skills.append(skill)

            tasks = await opsdroid.parse(Message("Hello", "user", "#general", None))
            self.assertEqual(len(tasks), 2)  # match_always and the skill

            tasks = await opsdroid.parse(
                Message("Hello", "otheruser", "#general", None)
            )
            self.assertEqual(len(tasks), 1)  # Just match_always

            tasks = await opsdroid.parse(Message("Hello", "user", "#general", None))
            self.assertEqual(len(tasks), 2)  # match_always and the skill

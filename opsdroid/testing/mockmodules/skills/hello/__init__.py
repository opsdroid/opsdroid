"""A mocked skill."""

from opsdroid.skill import Skill
from opsdroid.matchers import match_regex


class TestSkill(Skill):
    """A mocked skill."""

    called = False

    @match_regex("hello")
    async def test_method(self, message):
        """A test method skill."""
        self.called = True
        await message.respond("hello")

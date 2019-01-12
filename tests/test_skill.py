import unittest
from unittest.mock import Mock

from opsdroid.__main__ import configure_lang
from opsdroid.matchers import match_regex
from opsdroid.skill import Skill


class _TestSkill(Skill):
    @property
    def erroneous_property(self):
        raise ValueError()

    @match_regex(r'hello')
    def hello_skill(self, message):
        message.respond('Hello')


class TestSkill(unittest.TestCase):
    """Test the opsdroid skill base class."""

    def setUp(self):
        configure_lang({})

    def test_init(self):
        config = {"example_item": "test"}
        skill = Skill(None, config)
        self.assertIsNone(skill.opsdroid)
        self.assertEqual("test", skill.config["example_item"])

    def test_init_erroneous_property(self):
        """Test that properties that raise an exception don’t mess up initialisation"""

        config = {"example_item": "test"}
        skill = _TestSkill(None, config)
        self.assertIsNone(skill.opsdroid)
        self.assertEqual("test", skill.config["example_item"])

    def test_matcher_on_instance(self):
        """Test that matchers get registered on an object instance, not just on the class"""

        skill = _TestSkill(None, None)
        self.assertTrue(hasattr(skill.hello_skill, 'matchers'))

    def test_matcher_called(self):
        """Test that if the decorated skill is called, the skill function gets called"""

        skill = _TestSkill(None, None)
        message = Mock()
        skill.hello_skill(message)

        self.assertTrue(message.respond.called_once)

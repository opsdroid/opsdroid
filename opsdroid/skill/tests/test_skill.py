"""Test the opsdroid skill."""
from asynctest.mock import Mock

from opsdroid.cli.start import configure_lang
from opsdroid.matchers import match_regex
from opsdroid.skill import Skill


class _TestSkill(Skill):
    @property
    def erroneous_property(self):
        raise ValueError()

    @match_regex(r"hello")
    def hello_skill(self, message):
        message.respond("Hello")


configure_lang({})


def test_init():
    config = {"example_item": "test"}
    skill = Skill(None, config)
    assert skill.opsdroid is None
    assert skill.config["example_item"] == "test"


def test_init_erroneous_property():
    """Test that properties that raise an exception don’t mess up initialisation."""

    config = {"example_item": "test"}
    skill = _TestSkill(None, config)
    assert skill.opsdroid is None
    assert skill.config["example_item"] == "test"


def test_matcher_on_instance():
    """Test that matchers get registered on an object instance, not just on the class."""

    skill = _TestSkill(None, None)
    assert hasattr(skill.hello_skill, "matchers")


def test_matcher_called():
    """Test that if the decorated skill is called, the skill function gets called."""

    skill = _TestSkill(None, None)
    message = Mock()
    skill.hello_skill(message)

    assert message.respond.called_once

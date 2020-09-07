"""Test the opsdroid parse_format parser."""
import asynctest.mock as amock

from opsdroid.cli.start import configure_lang
from opsdroid.matchers import match_parse
from opsdroid.events import Message
from opsdroid.parsers.parseformat import parse_format


configure_lang({})


async def getMockSkill():
    async def mockedskill(opsdroid, config, message):
        pass

    mockedskill.config = {}
    return mockedskill


async def test_parse_format_match_condition(opsdroid):

    mock_skill = await getMockSkill()
    opsdroid.skills.append(match_parse("Hello")(mock_skill))

    mock_connector = amock.CoroutineMock()

    message = Message("Hello world", "user", "default", mock_connector)
    skills = await parse_format(opsdroid, opsdroid.skills, message)
    assert len(skills) == 0

    message = Message("Hello", "user", "default", mock_connector)
    skills = await parse_format(opsdroid, opsdroid.skills, message)
    assert mock_skill == skills[0]["skill"]
    assert skills[0]["message"] is message
    # Test that the original object has had a new attribute added.
    assert hasattr(message, "parse_result")


async def test_parse_format_search_condition(opsdroid):

    mock_skill = await getMockSkill()
    opsdroid.skills.append(
        match_parse("Hello", matching_condition="search")(mock_skill)
    )

    mock_connector = amock.CoroutineMock()

    message = Message("Hello", "user", "default", mock_connector)
    skills = await parse_format(opsdroid, opsdroid.skills, message)
    assert mock_skill == skills[0]["skill"]

    message = Message("Hello world", "user", "default", mock_connector)
    skills = await parse_format(opsdroid, opsdroid.skills, message)
    assert mock_skill == skills[0]["skill"]


async def test_parse_format_parameters(opsdroid):

    mock_skill = await getMockSkill()
    opsdroid.skills.append(
        match_parse("say {text} {num:d} times", case_sensitive=False)(mock_skill)
    )

    mock_connector = amock.CoroutineMock()
    message = Message("Say hello 42 times", "user", "default", mock_connector)

    skills = await parse_format(opsdroid, opsdroid.skills, message)
    assert mock_skill == skills[0]["skill"]

    parsed_message = skills[0]["message"]
    assert parsed_message.parse_result["text"] == "hello"
    assert parsed_message.parse_result["num"] == 42

    assert len(parsed_message.entities.keys()) == 2
    assert "text" in parsed_message.entities.keys()
    assert parsed_message.entities["text"]["value"] == "hello"

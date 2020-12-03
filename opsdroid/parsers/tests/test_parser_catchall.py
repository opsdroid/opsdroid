"""Test the opsdroid catch-all parser."""

import logging

import asynctest.mock as amock
import pytest
from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.events import Message, OpsdroidStarted
from opsdroid.matchers import match_always, match_catchall
from opsdroid.parsers.catchall import parse_catchall

pytestmark = pytest.mark.asyncio

configure_lang({})


async def getMockSkill():
    async def mockedskill(config, message):
        pass

    mockedskill.config = {}
    return mockedskill


async def getRaisingMockSkill():
    async def mockedskill(config, message):
        raise Exception()

    mockedskill.config = {}
    return mockedskill


async def test_parse_catchall_decorator_parens():
    with OpsDroid() as opsdroid:
        mock_skill = await getMockSkill()
        opsdroid.skills.append(match_catchall()(mock_skill))
        opsdroid.run_skill = amock.CoroutineMock()

        mock_connector = amock.CoroutineMock()
        message = Message(
            text="Hello world",
            user="user",
            target="default",
            connector=mock_connector,
        )

        await parse_catchall(opsdroid, message)

        assert opsdroid.run_skill.called


async def test_parse_catchall_decorate_no_parens():
    with OpsDroid() as opsdroid:
        mock_skill = await getMockSkill()
        opsdroid.skills.append(match_catchall(mock_skill))
        opsdroid.run_skill = amock.CoroutineMock()

        mock_connector = amock.CoroutineMock()
        message = Message(
            text="Hello world",
            user="user",
            target="default",
            connector=mock_connector,
        )

        await parse_catchall(opsdroid, message)

        assert opsdroid.run_skill.called


async def test_parse_catchall_raises(caplog):
    caplog.set_level(logging.ERROR)
    with OpsDroid() as opsdroid:
        mock_skill = await getRaisingMockSkill()
        mock_skill.config = {"name": "greetings"}
        opsdroid.skills.append(match_catchall()(mock_skill))
        assert len(opsdroid.skills) == 1

        mock_connector = amock.MagicMock()
        mock_connector.send = amock.CoroutineMock()
        message = Message(
            text="Hello world",
            user="user",
            target="default",
            connector=mock_connector,
        )

        await parse_catchall(opsdroid, message)
        assert "ERROR" in caplog.text


async def test_parse_catchall_not_called():
    with OpsDroid() as opsdroid:
        mock_skill = await getMockSkill()
        catchall_skill = amock.CoroutineMock()
        opsdroid.skills.append(match_always()(mock_skill))
        opsdroid.skills.append(match_catchall()(catchall_skill))
        opsdroid.run_skill = amock.CoroutineMock()

        mock_connector = amock.CoroutineMock()
        message = Message(
            text="Hello world",
            user="user",
            target="default",
            connector=mock_connector,
        )

        await parse_catchall(opsdroid, message)

        assert not catchall_skill.called


async def test_parse_catchall_messages_only_default():
    with OpsDroid() as opsdroid:
        catchall_skill = await getMockSkill()
        event = OpsdroidStarted()
        opsdroid.skills.append(match_catchall()(catchall_skill))
        opsdroid.run_skill = amock.CoroutineMock()

        await parse_catchall(opsdroid, event)

        assert opsdroid.run_skill.called


async def test_parse_catchall_messages_only_enabled():
    with OpsDroid() as opsdroid:
        catchall_skill = await getMockSkill()
        event = OpsdroidStarted()
        opsdroid.skills.append(match_catchall(messages_only=True)(catchall_skill))
        opsdroid.run_skill = amock.CoroutineMock()

        mock_connector = amock.CoroutineMock()
        message = Message(
            text="Hello world",
            user="user",
            target="default",
            connector=mock_connector,
        )

        await parse_catchall(opsdroid, event)
        assert not opsdroid.run_skill.called
        await parse_catchall(opsdroid, message)
        assert opsdroid.run_skill.called

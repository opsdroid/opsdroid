import pytest
import asynctest.mock as amock

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.events import Message
from opsdroid.matchers import match_regex
from opsdroid import constraints

configure_lang({})  # Required for our internationalization of error messages


@pytest.fixture
def opsdroid():
    """An instance of the OpsDroid class."""
    with OpsDroid() as opsdroid:
        yield opsdroid


@pytest.fixture
def mock_skill():
    """A skill which does nothing but follows the skill API."""

    async def mockedskill(opsdroid, config, message):
        pass

    mockedskill.config = {}
    return mockedskill

@pytest.mark.asyncio
async def test_constrain_rooms_constrains(opsdroid, mock_skill):
    """Test that with the room constraint a skill is not called."""
    skill = match_regex(r".*")(mock_skill)
    skill = constraints.constrain_rooms(["#general"])(skill)
    opsdroid.skills.append(skill)

    tasks = await opsdroid.parse(
        Message(text="Hello", user="user", target="#random", connector=None)
    )
    assert len(tasks) == 2  # Just match_always and match_event

@pytest.mark.asyncio
async def def test_constrain_rooms_skips(opsdroid, mock_skill):
    """Test that with the room constraint a skill is not called."""
    skill = match_regex(r".*")(mock_skill)
    skill = constraints.constrain_rooms(["#general"])(skill)
    opsdroid.skills.append(skill)

    tasks = await opsdroid.parse(
        Message(text="Hello", user="user", target="#general", connector=None)
    )
    assert len(tasks) == 2  # Just match_always and match_event

@pytest.mark.asyncio
async def def test_constrain_rooms_inverted(opsdroid, mock_skill):
    skill = match_regex(r".*")(mock_skill)
    skill = constraints.constrain_rooms(["#general"], invert=True)(skill)
    opsdroid.skills.append(skill)

    tasks = await opsdroid.parse(
        Message(text="Hello", user="user", target="#general", connector=None)
    )
    assert len(tasks) == 2  # Just match_always and match_event

@pytest.mark.asyncio
async def def test_constrain_users_constrains(opsdroid, mock_skill):
    skill = match_regex(r".*")(mock_skill)
    skill = constraints.constrain_users(["user"])(skill)
    opsdroid.skills.append(skill)

    tasks = await opsdroid.parse(
        Message(text="Hello", user="otheruser", target="#general", connector=None)
    )
    assert len(tasks) == 2  # Just match_always and match_event

@pytest.mark.asyncio
async def def test_constrain_users_skips(opsdroid, mock_skill):
    skill = match_regex(r".*")(mock_skill)
    skill = constraints.constrain_users(["user"])(skill)
    opsdroid.skills.append(skill)

    tasks = await opsdroid.parse(
        Message(text="Hello", user="user", target="#general", connector=None)
    )
    assert len(tasks) == 2  # Just match_always and match_event

@pytest.mark.asyncio
async def def test_constrain_users_inverted(opsdroid, mock_skill):
    skill = match_regex(r".*")(mock_skill)
    skill = constraints.constrain_users(["user"], invert=True)(skill)
    opsdroid.skills.append(skill)

    tasks = await opsdroid.parse(
        Message(text="Hello", user="user", target="#general", connector=None)
    )
    assert len(tasks) == 2  # Just match_always and match_event

@pytest.mark.asyncio
async def def test_constrain_connectors_constrains(opsdroid, mock_skill):
    skill = match_regex(r".*")(mock_skill)
    skill = constraints.constrain_users(["slack"])(skill)
    opsdroid.skills.append(skill)
    connector = amock.Mock()
    connector.configure_mock(name="twitter")

    tasks = await opsdroid.parse(
        Message(text="Hello", user="user", target="#random", connector=None)
    )
    assert len(tasks) == 2  # Just match_always and match_event

@pytest.mark.asyncio
async def def test_constrain_connectors_skips(opsdroid, mock_skill):
    skill = match_regex(r".*")(mock_skill)
    skill = constraints.constrain_connectors(["slack"])(skill)
    opsdroid.skills.append(skill)
    connector = amock.Mock()
    connector.configure_mock(name="slack")

    tasks = await opsdroid.parse(
        Message(text="Hello", user="user", target="#general", connector=connector)
    )
    assert len(tasks) == 2  # Just match_always and match_event

@pytest.mark.asyncio
async def def test_constrain_connectors_inverted(opsdroid, mock_skill):
    skill = match_regex(r".*")(mock_skill)
    skill = constraints.constrain_connectors(["slack"], invert=True)(skill)
    opsdroid.skills.append(skill)
    connector = amock.Mock()
    connector.configure_mock(name="slack")

    tasks = await opsdroid.parse(
        Message(text="Hello", user="user", target="#general", connector=connector)
    )
    assert len(tasks) == 2  # Just match_always and match_event

@pytest.mark.asyncio
async def def test_constraint_can_be_called_after_skip(opsdroid, mock_skill):
    skill = match_regex(r".*")(mock_skill)
    skill = constraints.constrain_users(["user"])(skill)
    opsdroid.skills.append(skill)

    tasks = await opsdroid.parse(
        Message(text="Hello", user="user", target="#general", connector=None)
    )
    assert len(tasks) == 2  # Just match_always and match_event

    tasks = await opsdroid.parse(
         Message(text="Hello", user="otheruser", target="#general", connector=None
                )
    )
    assert len(tasks) == 2  # Just match_always and match_event

    tasks = await opsdroid.parse(
         Message(text="Hello", user="user", target="#general", connector=None
                )
    )
    assert len(tasks) == 2  # Just match_always and match_event

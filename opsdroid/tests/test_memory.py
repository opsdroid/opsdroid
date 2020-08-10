import pytest

from opsdroid.memory import Memory
from opsdroid.database import InMemoryDatabase


@pytest.fixture
def memory():
    mem = Memory()
    mem.databases = [InMemoryDatabase()]
    return mem


@pytest.mark.asyncio
async def test_memory(memory):
    data = "Hello world!"
    await memory.put("test", data)
    assert data == await memory.get("test")
    await memory.delete("test")
    assert await memory.get("test") is None


@pytest.mark.asyncio
async def test_empty_memory(memory):
    assert await memory.get("test") is None


@pytest.mark.asyncio
async def test_empty_memory_default(memory):
    assert await memory.get("test", "wibble") == "wibble"


@pytest.mark.asyncio
async def test_database_callouts(mocker, memory):
    memory.databases = [mocker.AsyncMock()]
    data = "Hello world!"

    await memory.put("test", data)
    assert memory.databases[0].put.called

    memory.databases[0].reset_mock()

    await memory.get("test")
    assert memory.databases[0].get.called

    memory.databases[0].reset_mock()
    await memory.delete("test")
    assert memory.databases[0].delete.called

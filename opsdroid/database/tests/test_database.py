import pytest

from opsdroid.database import Database


def test_init():
    """Test that the database is initialised properly."""
    config = {"example_item": "test"}
    database = Database(config)
    assert database.name == ""
    assert database.config["example_item"] == "test"


@pytest.mark.asyncio
async def test_connect():
    database = Database({})
    with pytest.raises(NotImplementedError):
        await database.connect()


@pytest.mark.asyncio
async def test_disconnect():
    database = Database({})
    try:
        await database.disconnect()
    except NotImplementedError:
        pytest.fail("disconnect() raised NotImplementedError unexpectedly!")


@pytest.mark.asyncio
async def test_get():
    database = Database({})
    with pytest.raises(NotImplementedError):
        await database.get("test")


@pytest.mark.asyncio
async def test_put():
    database = Database({})
    with pytest.raises(NotImplementedError):
        await database.put("test", {})


@pytest.mark.asyncio
async def test_delete():
    database = Database({})
    with pytest.raises(NotImplementedError):
        await database.delete("test")

import pytest

from opsdroid.database.postgresql import *


@pytest.fixture()
def database(config):
    return DatabasePostgresql(config)


@pytest.mark.parametrize("config", [{"database": "test_db"}])
def test_init(database):
    """Test that the database is initialised properly."""
    assert database.name == "postgresql"
    assert database.config["database"] == "test_db"


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{}])
async def test_connect(mocker, database):
    """Test that the mongo database has implemented connect function properly"""
    try:
        mocker.patch("asyncpg.connect", return_value=mocker.AsyncMock())
        await database.connect()
    except NotImplementedError:
        raise Exception
    else:
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"table": "test_table"}])
async def test_put(mocker, database):
    mocker.patch.object(database, "put_query", return_value={})
    mocker.patch("asyncpg.connect", return_value=mocker.AsyncMock())
    await database.connect()
    await database.put("test_key", {"value": "test_value"})


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"table": "test_table"}])
@pytest.mark.parametrize(
    "return_value",
    [
        [],
        [{"data": '{"value": "test_value"}'}],
        [{"data": '{"value": "test_value1"}'}, {"data": '{"value": "test_value2"}'}],
    ],
)
async def test_get(mocker, database, return_value):
    mocker.patch.object(database, "get_query", return_value=return_value)
    await database.get("test_key")


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"table": "test_table"}])
async def test_delete(mocker, database):
    mocker.patch.object(database, "delete_query", return_value={})
    await database.delete("test_key")

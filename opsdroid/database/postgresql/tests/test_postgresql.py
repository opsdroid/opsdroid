import pytest

from opsdroid.database.mockmodules.postgresql.postgresl_database import (
    DatabasePostgresqlConnectionMock,
)
from opsdroid.database.postgresql import DatabasePostgresql


@pytest.fixture()
def database(config):
    return DatabasePostgresql(config)


@pytest.fixture()
def mocked_connect_database(mocker, config):
    mocker.patch(
        "opsdroid.database.postgresql.DatabasePostgresql.connect", return_value=mocker.AsyncMock()
    )
    return DatabasePostgresql(config)


@pytest.fixture()
def mocked_database(database):
    database.connection = DatabasePostgresqlConnectionMock()
    return database


@pytest.mark.parametrize(
    "config", [{"database": "test_db", "table": "test_table"}]
)
def test_init(database):
    """Test that the database is initialised properly."""
    assert database.name == "postgresql"
    assert database.config["database"] == "test_db"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "config",
    [
        {},
        {
            "database": "test_db",
            "table": "test_table",
            "user": "root",
            "password": "postgresql",
        },
    ],
)
async def test_connect(database):
    """test that the postgresql database has implemented connect function properly"""
    try:
        await database.connect()
    except NotImplementedError:
        raise Exception
    else:
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"table": "test_table"}])
async def test_get(mocked_database):
    await mocked_database.get("test_key")


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"table": "test_table"}])
async def test_get2(mocker, mocked_connect_database):
    tables = {
        "test_table": DatabasePostgresqlConnectionMock({}),
        "new_table": DatabasePostgresqlConnectionMock({}),
    }
    async with mocked_connect_database.memory_in_table("new_table") as new_db:
        mocker.patch.object(new_db, "client", return_value=mocker.AsyncMock())
        new_db.database = tables
        await new_db.get("test_key")
        assert new_db.table == "new_table"


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"table": "test_table"}])
async def test_put(mocked_database):
    await mocked_database.put("test_key", {"key": "value"})


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"table": "test_table"}])
async def test_put2(mocked_database):
    await mocked_database.put("test_key", {})


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"table": "test_table"}])
async def test_put3(mocked_database):
    await mocked_database.put("test_key", "test_value")


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"table": "test_table"}])
async def test_delete(mocked_database):
    await mocked_database.delete("test_key")

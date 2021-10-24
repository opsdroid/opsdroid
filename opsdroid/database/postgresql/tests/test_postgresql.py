import pytest

from opsdroid.database.postgresql import DatabasePostgresql


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
@pytest.mark.parametrize("config", [{"table": "test_table"}, {"table": "test table"}])
async def test_put(mocker, database, transacted_postgresql_db):
    mocker.patch("asyncpg.connect", return_value=transacted_postgresql_db.connection)
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
async def test_get(mocker, database, return_value, transacted_postgresql_db):
    mocker.patch("asyncpg.connect", return_value=transacted_postgresql_db.connection)
    await database.get("test_key")


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"table": "test_table"}])
async def test_delete(mocker, database, transacted_postgresql_db):
    mocker.patch("asyncpg.connect", return_value=transacted_postgresql_db.connection)
    await database.delete("test_key")

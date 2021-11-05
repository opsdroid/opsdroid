import pytest

from opsdroid.database.mockmodules.mongo.mongo_database import (
    DatabaseMongoCollectionMock,
)
from opsdroid.database.mongo import DatabaseMongo


@pytest.fixture()
def database(config):
    return DatabaseMongo(config)


@pytest.fixture()
def mocked_connect_database(mocker, config):
    mocker.patch(
        "opsdroid.database.mongo.DatabaseMongo.connect", return_value=mocker.AsyncMock()
    )
    return DatabaseMongo(config)


@pytest.fixture()
def mocked_database(database):
    collection = database.collection
    database.database = {collection: DatabaseMongoCollectionMock({})}
    return database


@pytest.mark.parametrize(
    "config", [{"database": "test_db", "collection": "test_collection"}]
)
def test_init(database):
    """Test that the database is initialised properly."""
    assert database.name == "mongo"
    assert database.config["database"] == "test_db"
    assert database.config["collection"] == "test_collection"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "config",
    [
        {},
        {
            "database": "test_db",
            "collection": "test_collection",
            "protocol": "mongodb://",
            "port": "1234",
            "user": "root",
            "password": "mongo",
        },
    ],
)
async def test_connect(database):
    """Test that the mongo database has implemented connect function properly"""
    try:
        await database.connect()
        assert "mongodb://" in database.db_url
    except NotImplementedError:
        raise Exception
    else:
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_get(mocked_database):
    await mocked_database.get("test_key")


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_get2(mocker, mocked_connect_database):
    collections = {
        "test_collection": DatabaseMongoCollectionMock({}),
        "new_collection": DatabaseMongoCollectionMock({}),
    }
    async with mocked_connect_database.memory_in_collection("new_collection") as new_db:
        mocker.patch.object(new_db, "client", return_value=mocker.AsyncMock())
        new_db.database = collections
        await new_db.get("test_key")
        assert new_db.collection == "new_collection"


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_put(mocked_database):
    await mocked_database.put("test_key", {"key": "value"})


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_put2(mocked_database):
    await mocked_database.put("test_key", {})


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_put3(mocked_database):
    await mocked_database.put("test_key", "test_value")


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_delete(mocked_database):
    await mocked_database.delete("test_key")

import pytest

from opsdroid.database.mockmodules.mongo.mongo_database import DatabaseMongoCollectionMock
from opsdroid.database.mongo import DatabaseMongo


@pytest.fixture()
def database(config):
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
            "user": "root",
            "password": "mongo",
        },
    ],
)
async def test_connect(database):
    """Test that the mongo database has implemented connect function properly"""
    try:
        await database.connect()
    except NotImplementedError:
        raise Exception
    else:
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_get(mocked_database):
    mocked_database.database = {"test_collection": DatabaseMongoCollectionMock({})}
    try:
        await mocked_database.get("test_key")
    except Exception:
        raise Exception
    else:
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_put(mocked_database):
    mocked_database.database = {"test_collection": DatabaseMongoCollectionMock({})}
    try:
        await mocked_database.put("test_key", {"key": "value"})
    except Exception:
        raise Exception
    else:
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_put2(mocked_database):
    try:
        await mocked_database.put("test_key", {})
    except Exception:
        raise Exception
    else:
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_put3(mocked_database):
    try:
        await mocked_database.put("test_key", "test_value")
    except Exception:
        raise Exception
    else:
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_delete(mocked_database):
    try:
        await mocked_database.delete("test_key")
    except Exception:
        raise Exception
    else:
        pass

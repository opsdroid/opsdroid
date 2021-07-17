import pytest

from opsdroid.database.mockmodules.mongo.mongo_database import DatabaseMongoTest
from opsdroid.database.mongo import DatabaseMongo


@pytest.fixture()
def database(config):
    return DatabaseMongo(config)


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
async def test_get(database):
    database.database = {"test_collection": DatabaseMongoTest({})}
    with pytest.raises(TypeError):
        await database.get("test_db")


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_put(database):
    database.database = {"test_collection": DatabaseMongoTest({})}
    try:
        await database.put("test_key", {"key": "value"})
    except TypeError:
        try:
            await database.put("test_key", {})
        except NotImplementedError:
            raise Exception
        else:
            pass
    else:
        raise Exception


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_put2(database):
    try:
        await database.put("test_key", {})
    except TypeError:
        pass
    else:
        raise Exception


@pytest.mark.asyncio
@pytest.mark.parametrize("config", [{"collection": "test_collection"}])
async def test_delete(database):
    try:
        await database.delete("test_db")
    except TypeError:
        pass
    else:
        raise Exception

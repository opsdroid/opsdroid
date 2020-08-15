import asyncio
import json
import logging
from contextlib import suppress

import pytest

from opsdroid.database.redis import RedisDatabase
from opsdroid.helper import JSONEncoder


def return_async_value(val):
    f = asyncio.Future()
    f.set_result(val)
    return f


def test_init(caplog):
    caplog.set_level(logging.DEBUG)
    database = RedisDatabase({})
    assert None is database.client
    assert 0 == database.database
    assert "localhost" == database.host
    assert 6379 == database.port
    assert None is database.password

    log_iterator = iter(caplog.records)
    first_log = next(log_iterator)
    assert first_log.levelname == "DEBUG"


@pytest.mark.asyncio
async def test_connect(mocker, caplog):
    caplog.set_level(logging.DEBUG)
    database = RedisDatabase({})
    mocked_connection = mocker.patch("aioredis.create_pool")

    await database.connect()

    assert mocked_connection.called

    log_iterator = iter(caplog.records)
    first_log = next(log_iterator)
    assert first_log.levelname == "DEBUG"
    second_log = next(log_iterator)
    assert second_log.levelname == "INFO"


@pytest.mark.asyncio
async def test_connect_failure(mocker, caplog):
    caplog.set_level(logging.DEBUG)
    database = RedisDatabase({})
    mocked_connection = mocker.patch("aioredis.create_pool", side_effect=OSError)

    with suppress(OSError):
        await database.connect()

    assert mocked_connection.called

    log_iterator = iter(caplog.records)
    first_log = next(log_iterator)
    assert first_log.levelname == "DEBUG"
    second_log = next(log_iterator)
    assert second_log.levelname == "WARNING"


@pytest.mark.asyncio
async def test_get(mocker):
    database = RedisDatabase({})
    database.client = mocker.Mock()
    attrs = {"execute.return_value": return_async_value('{"data_key":"data_value"}')}
    database.client.configure_mock(**attrs)

    result = await database.get("key")

    assert result == dict(data_key="data_value")
    database.client.execute.assert_called_with("GET", "key")


@pytest.mark.asyncio
async def test_put(mocker):
    database = RedisDatabase({})
    database.client = mocker.Mock()
    attrs = {"execute.return_value": return_async_value("None")}
    database.client.configure_mock(**attrs)

    await database.put("key", dict(data_key="data_value"))

    database.client.execute.assert_called_with(
        "SET", "key", json.dumps(dict(data_key="data_value"), cls=JSONEncoder)
    )


@pytest.mark.asyncio
async def test_delete(mocker):
    database = RedisDatabase({})
    database.client = mocker.Mock()
    attrs = {"execute.return_value": return_async_value("None")}
    database.client.configure_mock(**attrs)

    await database.delete("key")

    database.client.execute.assert_called_with("DEL", "key")


@pytest.mark.asyncio
async def test_disconnect(mocker):
    database = RedisDatabase({})
    database.client = mocker.Mock()
    attrs = {"close.return_value": return_async_value("None")}
    database.client.configure_mock(**attrs)

    await database.disconnect()

    assert database.client.close.called

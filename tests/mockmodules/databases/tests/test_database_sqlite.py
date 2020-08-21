"""Tests for the DatabaseSqlite class."""
import pytest
import asyntest.mock as amock

import asyncio

from opsdroid.database.sqlite import DatabaseSqlite
from opsdroid.cli.start import configure_lang

    """A database test class.

    Test the opsdroid sqlite database class.

    """
configure_lang({})

def test_init():
"""Test initialisation of database class.

This method will test the initialisation of the database
class. It will assert if the database class properties are
declared.

"""
    database = DatabaseSqlite({"path": "sqlite.db"})
    assert database.client == None
    assert database.db_file == "sqlite.db"
    assert database.table == "opsdroid"
    assert database.conn_args == {"isolation_level": None} 

    """A async database test class.

    Test the async methods of the opsdroid sqlite database class.

    """
@pytest.mark.asyncio
async def test_connect():
"""Test database connection.

This method will test the database connection of sqlite database.
As the database is created `opsdroid` table is created first.

"""
    database = DatabaseSqlite({"path": "sqlite.db"})
    opsdroid = amock.CoroutineMock()
    opsdroid.eventloop = self.loop

    try:
        await database.connect()
        table = database.table
        client = type(database.client).__name__
        await database.disconnect()
    except NotImplementedError:
        raise Exception
    else:
        assert table == "opsdroid"
        assert client == "Connection"

@pytest.mark.asyncio
async def test_disconnect():
    """Test of database disconnection.

    This method will test the database disconnection of sqlite database.

    """
    database = DatabaseSqlite({"path": "sqlite.db"})
    opsdroid = amock.CoroutineMock()
    opsdroid.eventloop = self.loop

    try:
        await database.connect()
        await database.disconnect()
    except NotImplementedError:
        raise Exception
    else:
        pass

@pytest.mark.asyncio
async def test_get_put_and_delete():
"""Test get, put and delete functions of database

    This method will test the get, put and delete functions which help to read
    and write data from the database. The function `put` a value with
    key and asserts the same value after the `get` operation is completed
    followed by the `delete` operation which deletes the key.

"""
    database = DatabaseSqlite({"path": "sqlite.db"})
    opsdroid = amock.CoroutineMock()
    opsdroid.eventloop = self.loop

    try:
        await database.connect()
        table = database.table
        client = type(database.client).__name__
        await database.put("hello", {})
        data = await database.get("hello")
        await database.delete("hello")
        await database.disconnect()
    except NotImplementedError:
        raise Exception
    else:
        assert table == "opsdroid"
        assert data == {}
        assert client == "Connection"

@pytest.mark.asyncio
async def test_deprecated_path():
    database = DatabaseSqlite({"file": "sqlite.db"})
    assert database.db_file == "sqlite.db"

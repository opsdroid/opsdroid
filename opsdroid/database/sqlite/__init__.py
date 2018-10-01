"""A module for sqlite database."""
import os
import logging
import json
import datetime
import aiosqlite

from opsdroid.const import DEFAULT_ROOT_PATH
from opsdroid.database import Database


class DatabaseSqlite(Database):
    """A module for opsdroid to allow persist in a sqlite database."""

    def __init__(self, config):
        """Start the database connection."""
        super().__init__(config)
        logging.debug("Loaded sqlite database connector")
        self.name = "sqlite"
        self.config = config
        self.conn_args = {'isolation_level': None}
        self.db_file = None
        self.table = None

    async def connect(self, opsdroid):
        """Connect to the database."""
        self.db_file = self.config.get(
            "file", os.path.join(DEFAULT_ROOT_PATH, "sqlite.db"))
        self.table = self.config.get("table", "opsdroid")

        async with aiosqlite.connect(self.db_file, **self.conn_args) as _db:
            await _db.execute(
                "CREATE TABLE IF NOT EXISTS {}"
                "(key text PRIMARY KEY, data text)"
                .format(self.table)
            )
        logging.info("Connected to sqlite %s", self.db_file)

    async def put(self, key, data):
        """Insert or replace an object into the database for a given key."""
        logging.debug("Putting %s into sqlite", key)
        json_data = json.dumps(data, cls=JSONEncoder)
        async with aiosqlite.connect(self.db_file, **self.conn_args) as _db:
            cur = await _db.cursor()
            await cur.execute(
                "DELETE FROM {} WHERE key=?".format(self.table), (key,))
            await cur.execute(
                "INSERT INTO {} VALUES (?, ?)".format(self.table),
                (key, json_data))

    async def get(self, key):
        """Get data from the database for a given key."""
        logging.debug("Getting %s from sqlite", key)
        data = None
        async with aiosqlite.connect(self.db_file, **self.conn_args) as _db:
            cur = await _db.cursor()
            await cur.execute(
                "SELECT data FROM {} WHERE key=?".format(self.table), (key,))
            row = await cur.fetchone()
            if row:
                data = json.loads(row[0], object_hook=JSONDecoder())
        return data


class JSONEncoder(json.JSONEncoder):
    """Extended class to convert dict to JSON."""

    serializers = {}

    def default(self, obj):
        """Get marshaller of given type as parameter."""
        marshaller = self.serializers.get(
            type(obj), super(JSONEncoder, self).default)
        return marshaller(obj)


class JSONDecoder(object):
    """Class to convert JSON to dict."""

    decoders = {}

    def __call__(self, dct):
        """Get the respective decoder from the provided dict."""
        if dct.get('__class__') in self.decoders:
            return self.decoders[dct['__class__']](dct)
        return dct


def register_json_type(type_cls, fields, decode_fn):
    """Register new JSON types."""
    type_name = type_cls.__name__
    JSONEncoder.serializers[type_cls] = lambda obj: dict(
        __class__=type_name,
        **{field: getattr(obj, field) for field in fields}
    )
    JSONDecoder.decoders[type_name] = decode_fn


register_json_type(
    datetime.datetime,
    ['year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond'],
    lambda dct: datetime.datetime(
        dct['year'], dct['month'], dct['day'],
        dct['hour'], dct['minute'], dct['second'], dct['microsecond']
    )
)

register_json_type(
    datetime.date,
    ['year', 'month', 'day'],
    lambda dct: datetime.date(dct['year'], dct['month'], dct['day'])
)

register_json_type(
    datetime.time,
    ['hour', 'minute', 'second', 'microsecond'],
    lambda dct: datetime.time(
        dct['hour'], dct['minute'], dct['second'], dct['microsecond'])
)

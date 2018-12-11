"""A module for sqlite database."""
import os
import logging
import json
import datetime
import aiosqlite

from opsdroid.const import DEFAULT_ROOT_PATH
from opsdroid.database import Database

_LOGGER = logging.getLogger(__name__)

# pylint: disable=too-few-public-methods
# As the current module needs only one public method to register json types


class DatabaseSqlite(Database):
    """A sqlite database class.

    SQLite Database class used to persist data in sqlite.

    """

    def __init__(self, config, opsdroid=None):
        """Initialise the sqlite database.

        Set basic properties of the database. Initialise properties like
        name, connection arguments, database file, table name and config.

        Args:
            config (dict): The configuration of the database which consists
                           of `file` and `table` name of the sqlite database
                           specified in `configuration.yaml` file.

        """
        super().__init__(config, opsdroid=opsdroid)
        self.name = "sqlite"
        self.config = config
        self.conn_args = {'isolation_level': None}
        self.db_file = None
        self.table = None
        _LOGGER.debug(_("Loaded sqlite database connector"))

    async def connect(self):
        """Connect to the database.

        This method will connect to the sqlite database. It will create
        the database file named `sqlite.db` in DEFAULT_ROOT_PATH and set
        the table name to `opsdroid`. It will create the table if it does
        not exist in the database.

        Args:
            opsdroid (OpsDroid): An instance of opsdroid core.

        """
        self.db_file = self.config.get(
            "file", os.path.join(DEFAULT_ROOT_PATH, "sqlite.db"))
        self.table = self.config.get("table", "opsdroid")

        async with aiosqlite.connect(self.db_file, **self.conn_args) as _db:
            await _db.execute(
                "CREATE TABLE IF NOT EXISTS {}"
                "(key text PRIMARY KEY, data text)"
                .format(self.table)
            )

        self.client = _db
        _LOGGER.info(_("Connected to sqlite %s"), self.db_file)

    async def put(self, key, data):
        """Put data into the database.

        This method will insert or replace an object into the database for
        a given key. The data object is serialised into JSON data using the
        JSONEncoder class.

        Args:
            key (string): The key to store the data object under.
            data (object): The data object to store.

        """
        _LOGGER.debug(_("Putting %s into sqlite"), key)
        json_data = json.dumps(data, cls=JSONEncoder)

        async with aiosqlite.connect(self.db_file, **self.conn_args) as _db:
            cur = await _db.cursor()
            await cur.execute(
                "DELETE FROM {} WHERE key=?".format(self.table), (key,))
            await cur.execute(
                "INSERT INTO {} VALUES (?, ?)".format(self.table),
                (key, json_data))

        self.client = _db

    async def get(self, key):
        """Get data from the database for a given key.

        Args:
            key (string): The key to lookup in the database.

        Returns:
            object or None: The data object stored for that key, or None if no
                            object found for that key.

        """
        _LOGGER.debug(_("Getting %s from sqlite"), key)
        data = None

        async with aiosqlite.connect(self.db_file, **self.conn_args) as _db:
            cur = await _db.cursor()
            await cur.execute(
                "SELECT data FROM {} WHERE key=?".format(self.table),
                (key,))
            row = await cur.fetchone()
            if row:
                data = json.loads(row[0], object_hook=JSONDecoder())

        self.client = _db
        return data


class JSONEncoder(json.JSONEncoder):
    """A extended JSONEncoder class.

    This class is customised JSONEncoder class which helps to convert
    dict to JSON. The datetime objects are converted to dict with fields
    as keys.

    """

    # pylint: disable=method-hidden
    # See https://github.com/PyCQA/pylint/issues/414 for reference

    serializers = {}

    def default(self, o):
        """Convert the given datetime object to dict.

        Args:
            o (object): The datetime object to be marshalled.

        Returns:
            dict (object): A dict with datatime object data.

        Example:
            A dict which is returned after marshalling::

                {
                    "__class__": "datetime",
                    "year": 2018,
                    "month": 10,
                    "day": 2,
                    "hour": 0,
                    "minute": 41,
                    "second": 17,
                    "microsecond": 74644
                }

        """
        marshaller = self.serializers.get(
            type(o), super(JSONEncoder, self).default)
        return marshaller(o)


class JSONDecoder:
    """A JSONDecoder class.

    This class will convert dict containing datetime values
    to datetime objects.

    """

    decoders = {}

    def __call__(self, dct):
        """Convert given dict to datetime objects.

        Args:
            dct (object): A dict containing datetime values and class type.

        Returns:
            object or dct: The datetime object for given dct, or dct if
                             respective class decoder is not found.

        Example:
            A datetime object returned after decoding::

                datetime.datetime(2018, 10, 2, 0, 41, 17, 74644)

        """
        if dct.get('__class__') in self.decoders:
            return self.decoders[dct['__class__']](dct)
        return dct


def register_json_type(type_cls, fields, decode_fn):
    """Register JSON types.

    This method will register the serializers and decoders for the
    JSONEncoder and JSONDecoder classes respectively.

    Args:
        type_cls (object): A datetime object.
        fields (list): List of fields used to store data in dict.
        decode_fn (object): A lambda function object for decoding.

    """
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

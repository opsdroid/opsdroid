"""A mocked database module."""

from opsdroid.database.mongo import DatabaseMongo


class DatabaseMongoTest(DatabaseMongo):
    """The mocked database mongo class."""

    def __init__(self, config):
        """Start the class."""
        super().__init__(config)
        self.dummy_db = {}

    async def put(self, key, data):
        """Put a value to mocked database."""
        self.dummy_db[key] = data

    async def get(self, key):
        """Get a value from mocked database."""
        ret_value = None
        if key in self.dummy_db:
            ret_value = self.dummy_db[key]
        return ret_value

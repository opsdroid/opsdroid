"""A mocked database module."""


class DatabaseMongoTest:
    """The mocked database mongo class."""

    def __init__(self, config):
        """Start the class."""
        self.config = config
        self.dummy_db = {}

    async def find_one(self, key):
        """Mock method find_one.

        Args: key(object) not considered for test
        """
        return await self.dummy_db

    async def update_one(self, key, update):
        """Mock method update_one.

        Args: key(object) not considered for test
        """
        return await self.dummy_db

    async def insert_one(self, key):
        """Mock method insert_one.

        Args: key(object) not considered for test
        """
        return self.dummy_db

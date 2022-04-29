"""A mocked database module."""


class DatabaseMongoCollectionMock:
    """The mocked database mongo class."""

    def __init__(self, config):
        """Start the class."""
        self.config = config
        self.dummy_doc = {}
        self.valid_response = {"_id": 123, "key": "456", "value": "789"}

    async def find_one(self, key):
        """Mock method find_one.

        Args: key(object) not considered for test
        """
        return self.valid_response

    async def update_one(self, key, update, **kwargs):
        """Mock method update_one.

        Args: key(object) not considered for test
        """
        return self.dummy_doc

    async def delete_one(self, key):
        """Mock method delete_one.

        Args: key(object) not considered for test
        """
        return self.dummy_doc

"""A base class for databases to inherit from."""


class Database:
    """A base database.

    Database classes are used to persist key/value pairs in a database.

    """

    def __init__(self, config, opsdroid=None):
        """Create the database.

        Set some basic properties from the database config such as the name
        of this database. It could also be a good place to setup properties
        to hold things like the database connection object and the database
        name.

        Args:
            config (dict): The config for this database specified in the
                           `configuration.yaml` file.
            opsdroid (OpsDroid): An instance of opsdroid.core.

        """
        self.name = ""
        self.config = config
        self.opsdroid = opsdroid
        self.client = None
        self.database = None

    async def connect(self):
        """Connect to database service and store the connection object.

        This method should connect to the given database using a native
        python library for that database. The library will most likely involve
        a connection object which will be used by the put, get and delete methods.
        This object should be stored in self.

        """
        raise NotImplementedError

    async def disconnect(self):
        """Disconnect from the database.

        This method should disconnect from the given database using a native
        python library for that database.

        """

    async def put(self, key, data):
        """Store the data object in a database against the key.

        The data object will need to be serialised in a sensible way which
        suits the database being used and allows for reconstruction of the
        object.

        Args:
            key (string): The key to store the data object under.
            data (object): The data object to store.

        Returns:
            bool: True for data successfully stored, False otherwise.

        """
        raise NotImplementedError

    async def get(self, key):
        """Return a data object for a given key.

        Args:
            key (string): The key to lookup in the database.

        Returns:
            object or None: The data object stored for that key, or None if no
                            object found for that key.

        """
        raise NotImplementedError

    async def delete(self, key):
        """Delete a data object for a given key.

        Args:
            key (string): The key to delete in the database.

        Returns:
            object or None: The data object stored for that key, or None if no
                            object found for that key.

        """
        raise NotImplementedError


class InMemoryDatabase(Database):
    """A simple in memory implementation of the database API."""

    def __init__(self, config={}, opsdroid=None):  # noqa: D107
        super().__init__(config, opsdroid)
        self.memory = {}
        self.name = "inmem"

    async def connect(self):  # noqa: D102
        pass  # pragma: nocover

    async def get(self, key):  # noqa: D102
        return self.memory.get(key)

    async def put(self, key, value):  # noqa: D102
        self.memory[key] = value

    async def delete(self, key):  # noqa: D102
        if key in self.memory:
            del self.memory[key]

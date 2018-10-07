"""Class for persisting information in opsdroid."""

import logging


_LOGGER = logging.getLogger(__name__)


class Memory:
    """A Memory object.

    An object to obtain, store and persist data outside of opsdroid.

    Attributes:
        databases (:obj:`list` of :obj:`Database`): List of database objects.
        memory (:obj:`dict`): In-memory dictionary to store data.

    """

    def __init__(self):
        """Create object with minimum properties."""
        self.memory = {}
        self.databases = []

    async def get(self, key):
        """Get data object for a given key.

        Gets the key value found in-memory or from the database(s).

        Args:
            key (str): Key to retrieve data.

        Returns:
            A data object for the given key, otherwise `None`.

        """
        _LOGGER.debug(_("Getting %s from memory."), key)
        database_result = await self._get_from_database(key)
        if database_result is not None:
            self.memory[key] = database_result
        if key in self.memory:
            return self.memory[key]

        return None

    async def put(self, key, data):
        """Put a data object to a given key.

        Stores the key and value in memory and the database(s).

        Args:
            key (str): Key for the data to store.
            data (obj): Data object to store.

        """
        _LOGGER.debug(_("Putting %s to memory"), key)
        self.memory[key] = data
        await self._put_to_database(key, self.memory[key])

    async def _get_from_database(self, key):
        """Get updates from databases for a given key.

        Gets the first key value found from the database(s).

        Args:
            key (str): Key to retrieve data from a database.

        Returns:
            The first key value (data object) found from the database(s).
            Or `None` when no database is defined or no value is found.

        Todo:
            * Handle multiple databases

        """
        if not self.databases:
            return None

        results = []
        for database in self.databases:
            results.append(await database.get(key))
        return results[0]

    async def _put_to_database(self, key, data):
        """Put updates into databases for a given key.

        Stores the key and value on each database defined.

        Args:
            key (str): Key for the data to store.
            data (obj): Data object to store.

        """
        if self.databases:
            for database in self.databases:
                await database.put(key, data)

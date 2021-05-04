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
        self.databases = []

    async def get(self, key, default=None, **kargs):
        """Get data object for a given key.

        Gets the key value found in-memory or from the database(s).

        Args:
            key (str): Key to retrieve data.

        Returns:
            A data object for the given key, otherwise `None`.

        """
        _LOGGER.debug(_("Getting %s from table %s in memory."), key, kwargs['table_name'])
        result = await self._get_from_database(key, **kargs)
        return result or default

    async def put(self, key, data, **kargs):
        """Put a data object to a given key.

        Stores the key and value in memory and the database(s).

        Args:
            key (str): Key for the data to store.
            data (obj): Data object to store.

        """
        _LOGGER.debug(_("Putting %s to table %s in memory."), key, kwargs['table_name'])
        await self._put_to_database(key, data, **kargs)

    async def delete(self, key):
        """Delete data object for a given key.

        Deletes the key value found in-memory or from the database(s).

        Args:
            key (str): Key to delete data.

        """
        _LOGGER.debug(_("Deleting %s from table %s in memory."), key, kwargs['table_name'])
        await self._delete_from_database(key)

    async def _get_from_database(self, key, **kargs):
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
            return None  # pragma: nocover

        results = []
        for database in self.databases:
            results.append(await database.get(key, **kargs))
        return results[0]

    async def _put_to_database(self, key, data, **kargs):
        """Put updates into databases for a given key.

        Stores the key and value on each database defined.

        Args:
            key (str): Key for the data to store.
            data (obj): Data object to store.

        """
        if self.databases:
            for database in self.databases:
                await database.put(key, data, **kargs)

    async def _delete_from_database(self, key):
        """Delete data from databases for a given key.

        Deletes the key and value on each database defined.

        Args:
            key (str): Key for the data to delete.

        """
        if self.databases:
            for database in self.databases:
                await database.delete(key)

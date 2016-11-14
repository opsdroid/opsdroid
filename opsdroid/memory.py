"""Class for persisting information in opsdroid."""

import logging


class Memory:
    """An object to store and persist data outside of opsdroid."""

    def __init__(self):
        """Create memory dictionary."""
        self.memory = {}
        self.databases = []

    async def get(self, key):
        """Get data object for a given key."""
        logging.debug("Getting " + key + " from memory")
        database_result = await self._get_from_database(key)
        if database_result is not None:
            self.memory[key] = database_result
        if key in self.memory:
            return self.memory[key]
        else:
            return None

    async def put(self, key, data):
        """Put a data object to a given key."""
        logging.debug("Putting " + key + " to memory")
        self.memory[key] = data
        await self._put_to_database(key, self.memory[key])

    async def _get_from_database(self, key):
        """Get updates from databases for a given key."""
        if not self.databases:
            logging.warning("No databases configured, data will not persist")
            return None
        else:
            results = []
            for database in self.databases:
                results.append(await database.get(key))
            # TODO: Handle multiple databases
            return results[0]

    async def _put_to_database(self, key, data):
        """Put updates into databases for a given key."""
        if not self.databases:
            logging.warning("No databases configured, data will not persist")
        else:
            for database in self.databases:
                await database.put(key, data)

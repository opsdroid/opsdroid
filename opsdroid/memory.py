"""Class for persisting information in opsdroid."""

import logging


class Memory:
    """An object to store and persist data outside of opsdroid."""

    def __init__(self):
        """Create memory dictionary."""
        self.memory = {}
        self.databases = []

    def get(self, key):
        """Get data object for a given key."""
        logging.debug("Getting " + key + " from memory")
        database_result = self._get_from_database(key)
        if database_result is not None:
            self.memory[key] = database_result
        if key in self.memory:
            return self.memory[key]
        else:
            return None

    def put(self, key, data):
        """Put a data object to a given key."""
        logging.debug("Putting " + key + " to memory")
        self.memory[key] = data
        self._put_to_database(key, self.memory[key])

    def _get_from_database(self, key):
        """Get updates from databases for a given key."""
        if not self.databases:
            logging.warning("No databases configured, data will not persist")
            return None
        else:
            results = []
            for database in self.databases:
                results.append(database.get(key))
            # TODO: Handle multiple databases
            return results[0]

    def _put_to_database(self, key, data):
        """Put updates into databases for a given key."""
        if not self.databases:
            logging.warning("No databases configured, data will not persist")
        else:
            for database in self.databases:
                database.put(key, data)

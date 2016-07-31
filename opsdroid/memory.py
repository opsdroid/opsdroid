"""Class for persisting information in opsdroid."""

import logging


class Memory:
    """An object to store and persist data outside of opsdroid."""

    def __init__(self):
        """Create memory dictionary."""
        self.memory = {}
        self.databases = []
        self.sync()

    def get(self, key):
        """Get data object for a given key."""
        logging.debug("Getting " + key + " from memory")
        self.sync()
        if key in self.memory:
            return self.memory[key]
        else:
            return None

    def put(self, key, data):
        """Put a data object to a given key."""
        logging.debug("Putting " + key + " to memory")
        self.memory[key] = data
        self.sync()

    def sync(self):
        """Sync memory with databases."""
        # TODO sync self.memory with databases in self.databases
        if not self.databases:
            logging.warning("No databases configured, data will not persist")
        else:
            pass

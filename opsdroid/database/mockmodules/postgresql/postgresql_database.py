"""A mocked Postgresql database module."""
import re

class DatabasePostgresqlConnectionMock:
    """The mocked database PostgreSQL connection class."""
    def __init__(self, config):
        """Start the class."""
        self.config = config

    async def disconnect(self):
        pass

    async def transaction(self):
        """Execute queries are ran in these instances"""
        pass

    async def execute(self, sql_query)
        #need something smart here
        #regex for the basic commands?
        pass
    
    async def fetch(self, sql_query):
        #need something smart here
        #regex for the only command it uses?
        #actually, there are a few - out of the DB
        pass

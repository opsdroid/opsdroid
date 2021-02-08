## Creating a custom database

Database classes are used to persist key/value pairs in a database. Values can be a complex object such as an array or a dictionary.

The class has three mandatory methods, `connect`, `put` and `get`.

#### connect
*connect* should initialise a connection to a database and store that connection object as a property of the database module instance.

#### put
*put* stores an object for a given key.

#### get
*get* returns an object for a given key. The object which is returned should be equivalent to the object which was stored.

#### delete
*delete* deletes an object for a given key.

```python
# We recommend you use the official library
# for your database and import it here
import databaselibrary

# Import opsdroid dependencies
from opsdroid.database import Database


class MyDatabase(Database):

  async def connect(self):
    # Create connection object for database
    self.connection = await databaselibrary.connect()

  async def put(self, key, value):
    # Insert the object into the database
    response = await self.connection.insert(key, value)

    # Return a bool for whether the insert was successful
    return response.success

  async def get(self, key):
    # Get the object from the database and return it
    return await self.connection.find(key)

  async def delete(self, key):
    # Delete the object from the database and return it
    return await self.connection.delete(key)

```

*If you need help or if you are unsure about something join our* [matrix channel](https://app.element.io/#/room/#opsdroid-general:matrix.org) *and ask away! We are more than happy to help you.*

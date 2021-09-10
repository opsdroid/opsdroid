# MongoDB

A database module for [opsdroid](https://github.com/opsdroid/opsdroid) to persist memory in a [mongo database](https://www.mongodb.com/).

## Requirements

An accessible MongoDB server with the database that you provide already created.

## Configuration

```yaml
databases:
  mongo:
    host:                       "my_host"       # (optional) default "localhost"
    port:                       "12345"         # (optional) default "27017"
    database:                   "my_database"   # (optional) default "opsdroid"
    collection:                 "my_collection" # (optional) default "opsdroid"
    user:                       "my_user"       # (optional)
    password:                   "pwd123!"       # (optional)
```

## Usage
This module helps opsdroid to persist memory using a MongoDB database.

If desired, you can specify a default collection in the database configuration, but specify a different collection per call. Code that doesn't specify a collection name will be placed into the collection specified in the mongo database configuration.
```python
await opsdroid.memory.put(key, value, collection_name='example_collection')
await opsdroid.memory.get(key, collection_name='example_collection')
```

An addition to the usual use of memory, the mongo database provides a context manager `memory_in_collection` to perform some operations in a collection other than the one specified in the configuration.

```
db = opsdroid.get_database("mongo")
async with db.memory_in_colection("new_collection") as new_db:
    await new_db.put("key", "value")
    await new_db.get("key")
    await new_db.delete("key")
   ...
```

```eval_rst
.. automethod:: opsdroid.database.mongo.DatabaseMongo.memory_in_collection
```

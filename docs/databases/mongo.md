# MongoDB

A database module for [opsdroid](https://github.com/opsdroid/opsdroid) to persist memory in a [mongo database](https://www.mongodb.com/).

## Requirements

An accessible MongoDB server with the database that you provide already created.

## Configuration

```yaml
databases:
  mongo:
    host:                       "my_host"         # (optional) default "localhost"
    port:                       "12345"           # (optional) default "27017"
    database:                   "my_database"     # (optional) default "opsdroid"
    protocol:                   "mongodb://"      # (optional) default "mongodb://"
    collection:                 "my_collection"   # (optional) default "opsdroid"
    user:                       "my_user"         # (optional)
    password:                   "pwd123!"         # (optional)
```

## Usage
This module helps opsdroid to persist memory using a MongoDB database.

```python
await opsdroid.memory.put(key, value)
await opsdroid.memory.get(key)
await opsdroid.memory.delete(key)
```

In addition to the usual use of memory, the mongo database provides a context manager `memory_in_collection` to perform some operations in a collection other than the one specified in the configuration.

```
async with opsdroid.get_database("mongo").memory_in_colection("new_collection") as new_db:
    await new_db.put("key", "value")
    await new_db.get("key")
    await new_db.delete("key")
   ...
```

```eval_rst
.. automethod:: opsdroid.database.mongo.DatabaseMongo.memory_in_collection
```

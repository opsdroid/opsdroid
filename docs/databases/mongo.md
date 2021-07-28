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
    default_collection_name:    "my_collection" # (optional) default "opsdroid"
    user:                       "my_user"       # (optional)
    password:                   "pwd123!"       # (optional)
```

_Note_: You can also use `default_table_name` if you'd like to specify the collection just to stay consistent with SQL-based databases.

## Usage
This module helps opsdroid to persist memory using a MongoDB database.

If desired, you can specify a default collection in the database configuration, but specify a different collection per call. Code that doesn't specify a collection name will be placed into the collection specified in the mongo database configuration.
```python
await opsdroid.memory.put(key, value, collection_name='example_collection')
await opsdroid.memory.get(key, collection_name='example_collection')
```

_Note_: You can also use `table_name` if you'd like just to stay consistent with SQL-based databases.

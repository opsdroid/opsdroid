# PostgreSQL

A database module for [opsdroid](https://github.com/opsdroid/opsdroid) to persist memory in a [postgresql database](https://www.postgresql.org/).

## Requirements
An accessible PostgreSQL server with the database that you provide already created.
And `asyncpg` installed for making the requests. Note this package is pre-installed in the docker container.

## Configuration

```yaml
databases:
  postgresql:
    host:       "hostname" # (optional) default: "localhost"
    port:       5432 # (optional) default: 5432
    user:       "opsdroid" # (optional) default: "opsdroid"
    password:   "Please change me"
    database:   "opsdroid_db" # (optional) default: "opsdroid"
    table:      "opsdroid_table" # (optional) default: "opsdroid"
```

## Usage
This module helps opsdroid to persist memory using a PostgreSQL database.

```python
await opsdroid.memory.put("key", "value")
await opsdroid.memory.get("key")
await opsdroid.memory.delete("key")
```

This database module expects the table structure to contain the following fields:
```
field_name  type
-----------------
key         text
data        jsonb
```
If the specified table does not exist, this module will attempt to create it with this structure.

The `value` parameter provided to in the `put` example can either be a string or a json object. If a string is provided, it will be translated to a json object, i.e. `{"value": "the input string"}`. If a json object is provided, it will be stored as is.

In the `get` operation, if the only key contained in the `data` object is `value`, then only the string will be returned. Otherwise, the entire json object will be returned.

In addition to the usual use of memory, the postgresql database provides a context manager `memory_in_table` to perform operations in tables other than the one specified in the configuration.

```python
async with opsdroid.get_database("postgresql").memory_in_table("new_table") as new_db:
    await new_db.put("key", "value")
    await new_db.get("key")
    await new_db.delete("key")
   ...
```

```eval_rst
.. automethod:: opsdroid.database.postgresql.DatabasePostgresql.memory_in_table
```

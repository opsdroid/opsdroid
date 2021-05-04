# PostgreSQL

A database module for [opsdroid](https://github.com/opsdroid/opsdroid) to persist memory in a [postgres database](https://www.postgresql.org/).

## Requirements
An accessible PostgreSQL server with the database that you provide already created.
And `asyncpg` installed for making the requests. Note this package is pre-installed in the docker container.

## Configuration

```yaml
databases:
  postgresql:
    host: "hostname"
    port: 5432
    user: opsdroid
    password: "Please change me"
    database: opsdroid_db
```

## Usage
This database connector is unique at the time of writing in it's ability to use different tables to place the key value pairs into. This is optional. Code that doesn't specify a table name will be placed into `opsdroid_default`.
```python
await opsdroid.memory.put(key, value, table_name='example_table')
await opsdroid.memory.get(key, table_name='example_table')
```
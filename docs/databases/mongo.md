# MongoDB

A database module for [opsdroid](https://github.com/opsdroid/opsdroid) to persist memory in a [mongo database](https://www.mongodb.com/).

## Requirements

None.

## Configuration

```yaml
databases:
  mongo:
    host:       "my_host"     # (optional) default "localhost"
    port:       "12345"       # (optional) default "27017"
    database:   "my_database" # (optional) default "opsdroid"
    user:       "my_user"     # (optional)
    password:   "pwd123!"     # (optional)
```

## Usage
This module helps opsdroid to persist memory using an MongoDB database.

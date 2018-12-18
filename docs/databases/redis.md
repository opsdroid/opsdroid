# opsdroid redis database

A database module for [opsdroid](https://github.com/opsdroid/opsdroid) to persist memory in a [redis database](https://redis.io/).

## Configuration

```yaml
databases:
  - name: redis
    host:       "my host"     # (optional) default "localhost"
    port:       "12345"       # (optional) default "6379"
    database:   "7"           # (optional) default "0"
    password:   "pass123"     # (optional) default "None"
```

## Usage
This module helps opsdroid to persist memory using a redis database.

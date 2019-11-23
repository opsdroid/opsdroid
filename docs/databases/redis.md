# Redis

A database module for [opsdroid](https://github.com/opsdroid/opsdroid) to persist memory in a [redis database](https://redis.io/).

## Requirements

None.

_Note: If you want to use redis locally you should have the `redis cli` installed in your machine and running, otherwise the database will fail to connect._

## Configuration

```yaml
databases:
  redis:
    host:       "my host"     # (optional) default "localhost"
    port:       "12345"       # (optional) default "6379"
    database:   7           # (optional) default 0
    password:   "pass123"     # (optional) default "None"
    reconnect:  true          # (optional) default "False"
```

## Usage
This module helps opsdroid to persist memory using a redis database.

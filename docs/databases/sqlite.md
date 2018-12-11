# SQLite Database Module

A database module for opsdroid to persist memory in a [SQLite](https://www.sqlite.org/) database.

## Configuration

```yaml
databases:
  - name: sqlite
    file: "my_file.db"  # (optional) default "~/.opsdroid/sqlite.db"
    table: "my_table"  # (optional) default "opsdroid"
```

## Usage
This module helps opsdroid to persist memory using an SQLite database.

# Matrix

A database module for [opsdroid](https://github.com/opsdroid/opsdroid) to persist memory in a [matrix](https://matrix.org/) room in the form of state events. The data can be encrypted by storing them as room events in encrypted rooms.

## Requirements

None.

_Note: To use encryption you need the e2e dependencies for matrix-nio which can be installed with `pip install matrix-nio[e2e]`_

## Configuration

```yaml
databases:
  matrix:
    default_room: "main"
    single_state_key: "dev.opsdroid.database"
    should_encrypt: True
```

## Usage

The database provides 3 functions to interact with it - `get, put, and delete`.

The data is maintained in state events in the form of a dictionary. Each event
has a `state key` which is used to identify that event. You can configure the
database to have only one single state key or specify a state key for each
request. State events are sent to the room in the configuration.

The `get` function takes one argument, the key. If the database is configured to
have a single state key then the key should be the key for the dict in it or
`None` to get the entire dict. If single state key is disabled the the key
passed should be a dict in of the form `{state_key: key}` the key can be `None`
to return the entire dict.

The `put` function takes 2 arguments, the key and value to put in the
dictionary. The key is either the dict key if single state key is set or the
state key if single state key is not set. if single state key is not set then
the value needs to be a dict of the form `{key: value}`. 

the `delete` function takes one argument, the key to delete. Same usage as `get`
except you cannot delete the entire dict. Pass a list of keys to delete
multiple keys.

The database provides a context manager `memory_in_room` to perform some
operations in a different rooms. use it as:
```
with memory_in_room(new_room_id):
	database ops
```

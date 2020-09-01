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
    single_state_key: True
    should_encrypt: True
```

## Usage

The database provides 3 functions to interact with it - `get, put, and delete`.

The data is maintained in state events in the form of a dictionary. Each event
has a `state key` which is used to identify that event. You can configure the
database to have only one single state key or specify a state key for each
request. State events are sent to the room specified in the configuration.

The `get` function takes one argument, the key. If the database is configured to
have a single state key then the key passed should be the key for the dict in it. If
single state key is disabled the the key passed should be the state key.

The `put` function takes 2 arguments, the key and value to put in the
dictionary. The key is either the dict key if single state key is set or the
state key if single state key is not set. The value can be whatever you want.

the `delete` function takes one argument, the key to delete. The key is either
the dict key if single state key is set or the state key if single state key is
not set. You can pass a list of keys to delete multiple keys if single state
key is enabled.

The database provides a context manager `memory_in_room` to perform some
operations in a different rooms. use it as:
```
db = opsdroid.get_database("matrix")
with db.memory_in_room(new_room_id):
	database ops
```

## Encryption

In encrypted Matrix rooms, state events (used by the database) are not encrypted. This means that anything put into the matrix database in an encrypted room would not be encrypted. To prevent this the matrix database send the **values** you put into your database into the room as regular events, which are encrypted, and then references these events from the database (which is still a state event).
This has two effects you should be aware of:

1) The keys in your database are not encrypted, **do not put sensitive information in the key**.

2) If opsdroid can't decrypt the event, it will be dropped from the database. This means that if you need long term storage in your encrypted rooms you must take steps to save the matrix connectors store (where the decryption keys are kept), so back up your store and keep it safe!

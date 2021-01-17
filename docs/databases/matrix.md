# Matrix

This database module stores the opsdroid memory into "state events" in a matrix room.
These state events form part of the history of the room and can be queried from the room at any time, like the rest of a room, they are replicated over all participating servers in the room, making them a robust way of storing json objects.

## Requirements

Install opsdroid with the `database_matrix` and `connector_matrix` extras to use the matrix database, also install with `connector_matrix_e2e` to use the connector and database in encrypted rooms.
The matrix connector must be configured to be able to use the matrix database, see that page of the docs for more information.

## Configuration

A minimal configuration is:

```yaml
databases:
  matrix:
```

In its default configuration the database will put events into the room named "main" in the connector configuration.

   
An example of all the configuration options, with their default values is:

```yaml
databases:
  matrix:
    default_room: main
    single_state_key: True
    should_encrypt: True
```

In general we recommend setting `single_state_key: False`, the default is `True` for backwards compatibility reasons but the downsides of setting it to `False` have now been removed.

## Usage

Interacting with opsdroid databases happens through opsdroid's memory, see the memory page for more details.

An addition to the usual use of memory, the matrix database provides a context manager `memory_in_room` to perform some operations in a different rooms.
The room can be specified with a matrix room alias, the name of a room in the connector config or a matrix room id.

```
db = opsdroid.get_database("matrix")
with db.memory_in_room(new_room):
   ...
```

```eval_rst
.. automethod:: opsdroid.database.matrix.DatabaseMatrix.memory_in_room
```

There is also a decorator for skill functions to use the memory of the room where the event was received from.
It uses the `.target` attribute of the third argument to the skill function, which is the matrix event.
```
from opsdroid.database.matrix import memory_in_event_room

@memory_in_event_room
async def skill_func(opsdroid, config, message):
	...
```

```eval_rst
.. autofunction:: opsdroid.database.matrix.memory_in_event_room
```

## How it Works

### State Events and State Keys

Matrix state events are used to store metadata about the room, such as its members, its name and topic.
The matrix database uses state events to store arbitary data you save to opsdroid memory.
In this section we describe a little about how this fits into the matrix protocol for those who are interested.

Matrix state events have three main components:
  * a type, which for the opsdroid matrix database is `dev.opsdroid.database`
  * a "state key" which distinguishes state events with the same type
  * content which is a json object

Matrix state events form a key value store where the key is a combination of the type and state event, i.e. `("dev.opdroid.database", "")` or `("dev.opsdroid.database", "reminders")`.

In the default configuration the state key is not used, the whole database is stored in a single json object in the content of the `dev.opsdroid.database` event with `state_key: ""`.
This means that if one key is changed then the whole event is resent.
When the ``single_state_key: False`` option is set, the key given to the opsdroid memory is used as the state key, this allows directly querying the matrix API for the value corresponding to that key.


### Encryption

In encrypted Matrix rooms, state events (used by the database) are not encrypted.
This means that anything put into the matrix database in an encrypted room would not be encrypted.
To prevent this the matrix database sends the **values** you put into your database into the room as regular events, which are encrypted, and then references these events from the database (which is still a state event).
This has two effects you should be aware of:

1) The keys in your database are not encrypted, **do not put sensitive information in the key**.

2) If opsdroid can't decrypt the event, it will be dropped from the database. This means that if you need long term storage in your encrypted rooms you must take steps to save the matrix connectors store (where the decryption keys are kept), so back up your store and keep it safe!

If you would rather your database not be encrypted in an encrypted room, you can set the `should_encrypt: False` config option.

# Matrix

Matrix is an open standard for secure, decentralised, real-time communication.
The matrix connector for opsdroid supports connecting to any matrix server and sending and receiving almost all supported events, including in end-to-end encrypted rooms.

## Requirements

To use this connector you will need to have:

  * A Matrix account for the bot with a username (mxid) and password.
  * Know what your [homeserver](https://matrix.org/faq/#what-is-a-homeserver%3F) (matrix server URL) is.
  * Know the room alias (address) for the room (or rooms) you want the bot to join.


## Configuration
A simple configuration looks like:

```yaml
connectors:
  matrix:
    # Required
    mxid: "@username:matrix.org"
    password: "mypassword"
    rooms:
      'main': '#matrix:matrix.org'
    # Optional
    homeserver: "https://matrix.org"
    nick: "Botty McBotface"  # The nick will be set on startup
```

The connector can be configured with any number of rooms, each given a name.
The first room should always be named "main" this room will be the one that messages will be sent to unless they are sent elsewhere.

The following code shows all the configuration options:

```yaml
connectors:
  matrix:
    # Required
    mxid: "@username:matrix.org"
    password: "mypassword"
    # A dictionary of rooms to connect to
    # One of these have to be named 'main'
    rooms:
      'main': '#matrix:matrix.org'
      'other': '#element-web:matrix.org'
    # Optional
    homeserver: "https://matrix.org"
    nick: "Botty McBotface"  # The nick will be set on startup
    room_specific_nicks: False  # Look up room specific nicknames of senders (expensive in large rooms)
    device_name: "opsdroid"
    enable_encryption: False
    device_id: "opsdroid" # A unique string to use as an ID for a persistent opsdroid device
    store_path: "path/to/store/" # Path to the directory where the matrix store will be saved
```


## End to End Encryption

```eval_rst
.. note::
    mxid & password must be used for E2EE to work
```

To be able to use E2EE you need to have the 'olm' library installed, this is currently not available through pip, you can find it [here](https://gitlab.matrix.org/matrix-org/olm/), in most linux distributions or by using the opsdroid Docker images.

``eval_rst
.. note::
    Opsdroid >= v0.24.1 Docker image includes E2EE
```

Once olm is installed you need to install opsdroid with the ``connector_matrix_e2e`` extra (by running ``pip install opsdroid[connector_matrix_e2e]``, this is not done by default as it required you to have already installed the olm library.
You also need to set the `enable_encryption: True` configuration option to enable encryption.
The connector supports interacting with end to end encrypted rooms for which it will create a sqlite database to store the encryption keys into, where this database is kept can be configured with ``store_path``.
Currently there is no device verification implemented which means messages will be sent regardless of whether encrypted rooms have users with unverified devices.

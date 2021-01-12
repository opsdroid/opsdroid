# Events

Events in opsdroid represent things that happen on the services that opsdroid connects to.
They are both sent and received by the connectors.

All events are a subclass of the base `Event` class. Each event also defines its own set of attributes which are specific to that type of event.


### `Event`

The base `Event` class has the following attributes and methods.

```eval_rst
.. autoclass:: opsdroid.events.Event
   :members:
```
Note: For the sake of flexibility, Opsdroid only supports a single user on any given event. If you use Slack's (or any other chat platforms supported by Opsdroid that have the possibility of a single event corresponding to multiple users) API call to invite users to a channel, the API call takes a list of users as the input. In that case, you need to create multiple 'single-user' events instead of trying to create one 'multi-user' event. If concerned about the performance, the Skill can call the API directly rather than emitting multiple events.

### `OpsdroidStarted`

The `OpsdroidStarted` event is triggered once Opsdroid's loader has completed.
Skills can respond to this in order to perform startup actions which require connectors, databases, etc. to be available first.

```eval_rst
.. autoclass:: opsdroid.events.OpsdroidStarted
   :members:
   :inherited-members:
```

### `Message`

The `Message` object is the most common event type, it represents textual events, and has the following attributes in addition to the base `Event` attributes.

```eval_rst
.. autoclass:: opsdroid.events.Message
   :members:
   :inherited-members:
```

### `Typing`

An event to represent a typing indication.

```eval_rst
.. autoclass:: opsdroid.events.Typing
   :members:
   :inherited-members:
```

### `Reaction`

A reaction to a message, normally an emoji or a string representing one.


```eval_rst
.. autoclass:: opsdroid.events.Reaction
   :members:
   :inherited-members:
```

### `File`

A file event. All files should be representable as bytes. A `File` can be constructed using either a url or a `bytes` object, if a url is specified the `File.file_bytes` property will retrieve the url and store the response as `bytes`.


```eval_rst
.. autoclass:: opsdroid.events.File
   :members:
   :inherited-members:
```

### `Image`

The `Image` event is a subclass of `File`, so in the same way `File` can an `Image` can be either a url or bytes, but should always be representable as `bytes`.

```eval_rst
.. autoclass:: opsdroid.events.Image
   :members:
   :inherited-members:
```

### `Video`

The `Video` event is a subclass of `File`, so in the same way `File` can an `Video` can be either a url or bytes, but should always be representable as `bytes`.

```eval_rst
.. autoclass:: opsdroid.events.Video
   :members:
   :inherited-members:
```

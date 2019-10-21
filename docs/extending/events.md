# Events

Events in opsdroid represent things that happen on the services that opsdroid connects to.
They are both sent and received by the connectors.

All events are a subclass of the base `Event` class. Each event also defines its own set of attributes which are specific to that type of event.


### `Event`

The base `Event` class has the following attributes and methods:


#### Attributes
* `user`: A string containing the username of the user who wrote the message.

* `target`: A string normally containing the name of the room or chat channel the message was sent in.

* `connector`: A pointer to the opsdroid _connector object_ which received the message.

* `linked_event`: Another event linked to this one, for example the event that a `Message` replies to.

* `created`: A timestamp of when this event was instantiated.

* `event_id`: A unique identifier for this event as provided by the connector.

* `raw_event`: The raw event received by the connector (may be `None`).

* `raw_parses`: The raw response provided by the parser service.

* `responded_to`: A boolean (True/False) flag indicating if this event has already had its `respond` method called.

* `entities`: A dictionary mapping of entities created by parsers. These could be values extracted form sentences like locations, times, people, etc.


#### Methods
* `respond(event)`: A method which takes another `Event` object responds using any attributes of the event which are not overridden in the response `event`. i.e. if the `target` attribute on the `event` argument is `None` then the `target` of the event being responded to will be used.

### OpsdroidStarted

The `OpsdroidStarted` event is triggered once Opsdroid's loader has completed.
Skills can respond to this in order to perform startup actions which require connectors, databases, etc. to be available first.

### `Message`

The `Message` object is the most common event type, it represents textual events, and has the following attributes in addition to the base `Event` attributes.


#### Attributes

* `text`: The textual content of the message.

#### Methods
* `respond(text)`: The same as the `Event.respond` method, with the addition of accepting a `str` argument, which will be converted into a `Message` event.

### `Typing`

An event to represent a typing indication.

#### Attributes

* `trigger`: Trigger typing on or off.
* `timeout`: Timeout on typing event.

### `Reaction`

A reaction to a message, normally an emoji or a string representing one.

#### Attributes

* `emoji`: The emoji to use as a reaction.

### `File`

A file event. All files should be representable as bytes. A `File` can be constructed using either a url or a `bytes` object, if a url is specified the `File.file_bytes` property will retrieve the url and store the response as `bytes`.

#### Attributes

* `url`: The url of the file, can be `None`.
* `file_bytes`: The file as a `bytes` object.

### `Image`

The `Image` event is a subclass of `File`, so in the same way `File` can an `Image` can be either a url or bytes, but should always be representable as `bytes`.

#### Attributes

* `url`: The url of the file, can be `None`.
* `image_bytes`: The image as a `bytes` object.

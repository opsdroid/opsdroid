import logging

import pytest

from nio.responses import SyncResponse

from opsdroid import events

from opsdroid.connector.matrix.tests.conftest import message_factory, sync_response

from opsdroid.connector.matrix.create_events import MatrixEventCreator


async def events_from_sync(events, connector):
    response = SyncResponse.from_dict(sync_response(events))
    return [m async for m in connector._parse_sync_response(response)]


def assert_event_properties(event, **kwargs):
    for attr, value in kwargs.items():
        assert getattr(event, attr) == value


@pytest.mark.add_response(
    "/_matrix/client/r0/rooms/!12345:localhost/state/m.room.member/@test:localhost",
    "GET",
    {"displayname": "test"},
)
@pytest.mark.add_response(
    "/_matrix/client/r0/rooms/!12345:localhost/state/m.room.member/@test:localhost",
    "GET",
    {"displayname": "test"},
)
@pytest.mark.matrix_connector_config(
    {"access_token": "hello", "rooms": {"main": "#test:localhost"}}
)
@pytest.mark.asyncio
async def test_receive_message(opsdroid, connector_connected, mock_api, caplog):
    events = await events_from_sync(
        [
            message_factory("Hello", "m.text", "@test:localhost"),
            message_factory("Hello2", "m.text", "@test:localhost"),
        ],
        connector_connected,
    )

    assert_event_properties(
        events[0],
        text="Hello",
        user_id="@test:localhost",
        user="test",
        target="!12345:localhost",
    )

    assert_event_properties(
        events[1],
        text="Hello2",
        user_id="@test:localhost",
        user="test",
        target="!12345:localhost",
    )

    assert len(caplog.record_tuples) == 0, caplog.records


@pytest.mark.matrix_connector_config(
    {"access_token": "hello", "rooms": {"main": "#test:localhost"}}
)
@pytest.mark.asyncio
async def test_get_nick_error(opsdroid, connector_connected, mock_api, caplog):
    events = await events_from_sync(
        [
            message_factory("Hello", "m.text", "@test:localhost"),
        ],
        connector_connected,
    )

    assert_event_properties(
        events[0],
        text="Hello",
        user_id="@test:localhost",
        user="@test:localhost",
        target="!12345:localhost",
    )

    assert len(caplog.record_tuples) == 1

    assert caplog.record_tuples == [
        (
            "opsdroid.connector.matrix.connector",
            logging.ERROR,
            "Error during getting display name from room state: unknown error (status code None)",
        )
    ]


@pytest.mark.add_response(
    "/_matrix/client/r0/rooms/!12345:localhost/state/m.room.member/@test:localhost",
    "GET",
    {"displayname": "test"},
)
@pytest.mark.matrix_connector_config(
    {"access_token": "hello", "rooms": {"main": "#test:localhost"}}
)
@pytest.mark.asyncio
async def test_invite_with_message(opsdroid, connector_connected, mock_api, caplog):
    events = [
        message_factory("Hello", "m.text", "@test:localhost"),
    ]

    sync_dict = sync_response(events)
    sync_dict["rooms"]["invite"] = {
        "!12345:localhost": {
            "invite_state": {
                "events": [
                    {
                        "content": {"displayname": "Test", "membership": "invite"},
                        "origin_server_ts": 1612718865588,
                        "sender": "@other:localhost",
                        "state_key": "@test:localhost",
                        "type": "m.room.member",
                        "event_id": "$NGAUv_hybVRv5jop5SdWyMW-fCJ66D5d4FMNtydCzw",
                    }
                ]
            }
        }
    }

    response = SyncResponse.from_dict(sync_dict)

    events = [m async for m in connector_connected._parse_sync_response(response)]

    assert_event_properties(
        events[0],
        user_id="@other:localhost",
        user="@other:localhost",
        target="!12345:localhost",
    )

    assert_event_properties(
        events[1],
        text="Hello",
        user_id="@test:localhost",
        user="test",
        target="!12345:localhost",
    )

    assert len(caplog.record_tuples) == 0, caplog.records


@pytest.mark.add_response(
    "/_matrix/client/r0/rooms/!636q39766251:example.com/context/$f3h4d129462ha:example.com",
    "GET",
    {
        "content": {
            "body": "filename.jpg",
            "info": {"h": 398, "mimetype": "image/jpeg", "size": 31037, "w": 394},
            "msgtype": "m.image",
            "url": "mxc://example.org/JWEIFJgwEIhweiWJE",
        },
        "event_id": "$f3h4d129462ha:example.com",
        "origin_server_ts": 1432735824653,
        "room_id": "!636q39766251:example.com",
        "sender": "@example:example.org",
        "type": "m.room.message",
        "unsigned": {"age": 1234},
    },
)
@pytest.mark.matrix_connector_config(
    {"access_token": "hello", "rooms": {"main": "#test:localhost"}}
)
@pytest.mark.asyncio
async def test_matrix_event_creator(opsdroid, connector_connected, mock_api, caplog):
    event = MatrixEventCreator(connector_connected).create_event_from_eventid(
        eventid="$f3h4d129462ha:example.com", roomid="!636q39766251:example.com"
    )

    assert isinstance(event, events.File)

    assert_event_properties(
        event,
        event_id="$f3h4d129462ha:example.com",
        room_id="!636q39766251:example.com",
        type="m.room.message",
    )


@pytest.mark.add_response(
    "/_matrix/client/r0/rooms/!636q39766251:example.com/context/$f3h4d129462ha:example.com",
    "GET",
    {"errcode": "M_NOT_FOUND", "error": "Event not found."},
)
@pytest.mark.matrix_connector_config(
    {"access_token": "hello", "rooms": {"main": "#test:localhost"}}
)
@pytest.mark.asyncio
async def test_matrix_event_creator_incorrect(
    opsdroid, connector_connected, mock_api, caplog
):
    event = MatrixEventCreator(connector_connected).create_event_from_eventid(
        eventid="$f3h4example.com", roomid="!636q39766251:example.com"
    )

    assert isinstance(event, str)

    assert_event_properties(
        event,
        event_id="$f3h4example.com",
    )

import logging

import pytest

from nio.responses import SyncResponse

from opsdroid.connector.matrix.tests.conftest import message_factory, sync_response


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

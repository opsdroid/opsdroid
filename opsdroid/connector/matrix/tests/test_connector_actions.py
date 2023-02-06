import pytest

from opsdroid import events


@pytest.mark.add_response(
    "/_matrix/client/r0/rooms/!12345:localhost/leave",
    "POST",
    {},
)
@pytest.mark.add_response(
    "/_matrix/client/r0/directory/room/#test:localhost",
    "GET",
    {
        "room_id": "!12345:localhost",
        "servers": ["localhost"],
    },
)
@pytest.mark.asyncio
async def test_leave_room(opsdroid, connector_connected, mock_api):
    await opsdroid.send(
        events.LeaveRoom(target="#test:localhost", connector=connector_connected)
    )
    assert mock_api.called("/_matrix/client/r0/rooms/!12345:localhost/leave")

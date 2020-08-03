from mock import call
import pytest

import nio

from opsdroid.connector.matrix import ConnectorMatrix
from opsdroid.core import OpsDroid
from opsdroid.database.matrix import DatabaseMatrix

from json import JSONEncoder


@pytest.fixture
def patched_send(mocker):
    return mocker.patch("nio.AsyncClient._send")


@pytest.fixture
def opsdroid_matrix():
    connector = ConnectorMatrix(
        {
            "rooms": {"main": "#test:localhost"},
            "mxid": "@opsdroid:localhost",
            "password": "hello",
            "homeserver": "http://localhost:8008",
        }
    )
    connector.room_ids = {"main": "!notaroomid"}
    api = nio.AsyncClient("https://notaurl.com", None)
    api.access_token = "arbitrarytoken"
    connector.connection = api

    with OpsDroid() as opsdroid:
        opsdroid.connectors.append(connector)
        yield opsdroid


def matrix_call(method, path, content=None):
    state_key = path.partition("dev.opsdroid.database/")[2]
    path += "?access_token=arbitrarytoken"
    if not content:
        return call(
            nio.RoomGetStateEventResponse,
            method,
            path,
            response_data=("dev.opsdroid.database", f"{state_key}", "!notaroomid"),
        )
    else:
        return call(
            nio.RoomPutStateResponse,
            method,
            path,
            JSONEncoder(separators=(",", ":")).encode(content),
            response_data=("!notaroomid",),
        )


@pytest.mark.asyncio
async def test_default_config(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse({}, "", "", "")

    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
                {"twim": {"hello": "world"}},
            ),
        ],
    )


@pytest.mark.asyncio
async def test_put_custom_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse({}, "", "", "")

    db = DatabaseMatrix({"single_state_key": "wibble"}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/wibble",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/wibble",
                {"twim": {"hello": "world"}},
            ),
        ],
    )


@pytest.mark.asyncio
async def test_single_state_key_false(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse({}, "", "", "")

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
                {"hello": "world"},
            ),
        ],
    )


@pytest.mark.asyncio
async def test_single_state_not_a_dict(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse({}, "", "", "")

    value = "world"
    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
                {"twim": value},
            ),
        ],
    )


@pytest.mark.asyncio
async def test_default_not_a_dict(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse({}, "", "", "")

    value = "world"
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    with pytest.raises(ValueError):
        await db.put("twim", value)


@pytest.mark.asyncio
async def test_default_update_different_value(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"hello": "world"}, "", "", ""
    )

    value = {"red": "pill"}
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
                {"hello": "world", "red": "pill"},
            ),
        ],
    )


@pytest.mark.asyncio
async def test_default_update_same_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"hello": "world"}, "", "", ""
    )

    value = {"hello": "bob"}
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
                value,
            ),
        ],
    )


@pytest.mark.asyncio
async def test_update_same_key_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": {"hello": "world"}}, "", "", ""
    )

    value = {"hello": "bob"}
    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
                {"twim": value},
            ),
        ],
    )


@pytest.mark.asyncio
async def test_default_update_same_key_value(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"hello": "world"}, "", "", ""
    )

    value = {"hello": "world"}
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            )
        ],
    )


@pytest.mark.asyncio
async def test_default_update_same_key_value_single_state_key(
    patched_send, opsdroid_matrix
):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": {"hello": "world"}}, "", "", ""
    )

    value = {"hello": "world"}
    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            )
        ],
    )


@pytest.mark.asyncio
async def test_default_update_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": "hello"}, "", "", ""
    )

    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("pill", "red")

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
                {"twim": "hello", "pill": "red"},
            ),
        ],
    )


@pytest.mark.asyncio
async def test_put_encrypted(patched_send, opsdroid_matrix, mocker):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            return nio.RoomGetStateEventResponse({}, "", "", "")
        else:
            return nio.RoomSendResponse("enceventid", "!notaroomid")

    patched_send.side_effect = side_effect
    mocker.patch("nio.client.async_client.uuid4", return_value="bigrandomuuid")

    db = DatabaseMatrix({"should_encrypt": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            ),
            call(
                nio.RoomSendResponse,
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/send/dev.opsdroid.database/bigrandomuuid?access_token=arbitrarytoken",
                '{"twim":{"hello":"world"}}',
                ("!notaroomid",),
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
                {"twim": {"encrypted_val": "enceventid"}},
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_get_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": "hello", "wibble": "wobble"}, "", "", ""
    )

    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get("twim")

    patched_send.assert_called_once_with(
        nio.RoomGetStateEventResponse,
        "GET",
        "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/?access_token=arbitrarytoken",
        response_data=("dev.opsdroid.database", "", "!notaroomid"),
    )

    assert data == "hello"


@pytest.mark.asyncio
async def test_get(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"hello": "world"}, "", "", ""
    )

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get({"twim": "hello"})

    patched_send.assert_called_once_with(
        nio.RoomGetStateEventResponse,
        "GET",
        "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim?access_token=arbitrarytoken",
        response_data=("dev.opsdroid.database", "twim", "!notaroomid"),
    )

    assert data == "world"


@pytest.mark.asyncio
async def test_get_no_key_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"wibble": "wobble"}, "", "", ""
    )

    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get("twim")

    assert data is None


@pytest.mark.asyncio
async def test_get_no_key_404(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventError({"errcode": 404})

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get("twim")

    assert data is None


@pytest.mark.asyncio
async def test_get_no_key_500(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventError({"code": 500})

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get("twim")

    assert data is None


@pytest.mark.asyncio
async def test_get_encrypted(patched_send, opsdroid_matrix):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            return nio.RoomGetStateEventResponse(
                {"twim": {"encrypted_val": "enceventid"}}, "", "", ""
            )
        else:
            event = nio.Event(
                {
                    "type": "dev.opsdroid.database",
                    "event_id": "enceventid",
                    "sender": "@someone:localhost",
                    "origin_server_ts": "2005",
                    "content": {"twim": "hello"},
                }
            )
            resp = nio.RoomGetEventResponse()
            resp.event = event
            return resp

    patched_send.side_effect = side_effect

    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get("twim")

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            ),
            call(
                nio.RoomGetEventResponse,
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/event/enceventid?access_token=arbitrarytoken",
            ),
        ],
    )

    assert data == "hello"


@pytest.mark.asyncio
async def test_connect(patched_send, opsdroid_matrix):
    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)

    await db.connect()


@pytest.mark.asyncio
async def test_room_switch(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"hello": "world"}, "", "", ""
    )
    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    with db.memory_in_room("!notanotherroom"):
        assert db.room == "!notanotherroom"
        data = await db.get("hello")

    patched_send.assert_called_once_with(
        nio.RoomGetStateEventResponse,
        "GET",
        "/_matrix/client/r0/rooms/%21notanotherroom/state/dev.opsdroid.database/?access_token=arbitrarytoken",
        response_data=("dev.opsdroid.database", "", "!notanotherroom"),
    )

    assert db.room == "main"
    assert data == "world"


@pytest.mark.asyncio
async def test_migrate_and_errors(patched_send, opsdroid_matrix, mocker, caplog):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateResponse:
            return nio.RoomGetStateResponse(
                [
                    {
                        "type": "opsdroid.database",
                        "state_key": "",
                        "event_id": "roomeventid",
                        "content": {"hello": "world"},
                    }
                ],
                "!notaroomid",
            )
        else:
            return nio.RoomGetStateEventError(message="testing")

    patched_send.side_effect = side_effect
    mocker.patch("nio.client.async_client.uuid4", return_value="bigrandomuuid")

    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)
    caplog.clear()
    await db.put("hello", "world")

    patched_send.assert_has_calls(
        [
            call(
                nio.RoomGetStateResponse,
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state?access_token=arbitrarytoken",
                response_data=("!notaroomid",),
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
                {"hello": "world"},
            ),
            call(
                nio.RoomRedactResponse,
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/redact/roomeventid/bigrandomuuid?access_token=arbitrarytoken",
                "{}",
                response_data=("!notaroomid",),
            ),
        ],
    )

    assert ["Error putting key into matrix room !notaroomid: testing(None)"] == [
        rec.message for rec in caplog.records
    ]

    patched_send.side_effect = [
        nio.RoomGetStateError(message="testing"),
        nio.RoomGetStateEventError(message="testing"),
    ]
    caplog.clear()
    db.should_migrate = True
    await db.get("hello")

    assert [
        "Error migrating from opsdroid.database to dev.opsdroid.database in room !notaroomid: testing(None)",
        "Error getting hello from matrix room !notaroomid: testing(None)",
    ] == [rec.message for rec in caplog.records]

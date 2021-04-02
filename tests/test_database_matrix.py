from json import JSONEncoder

import nio
import pytest
from mock import AsyncMock, call

from opsdroid.connector.matrix.connector import ConnectorMatrix, MatrixException
from opsdroid.core import OpsDroid
from opsdroid.database.matrix import DatabaseMatrix, memory_in_event_room
from opsdroid.events import Message
from opsdroid.cli.start import configure_lang  # noqa


@pytest.fixture
def patched_send(mocker):
    return mocker.patch("nio.AsyncClient._send")


@pytest.fixture
def patched_uuid(mocker):
    return mocker.patch("nio.client.async_client.uuid4", return_value="bigrandomuuid")


@pytest.fixture
def opsdroid_matrix(mocker):
    connector = ConnectorMatrix(
        {
            "rooms": {"main": "#test:localhost"},
            "mxid": "@opsdroid:localhost",
            "password": "hello",
            "homeserver": "http://localhost:8008",
            "enable_encryption": True,
        }
    )
    connector.room_ids = {"main": "!notaroomid"}
    api = nio.AsyncClient("https://notaurl.com", None)
    api.access_token = "arbitrarytoken"
    api.store = mocker.AsyncMock
    api.store.load_encrypted_rooms = mocker.MagicMock(return_value=["!notaroomid"])
    connector.connection = api

    with OpsDroid() as opsdroid:
        opsdroid.connectors.append(connector)
        yield opsdroid


def matrix_call(method, path, content=None):
    state_key = path.partition("dev.opsdroid.database/")[2]
    if content is None:  # could be empty dict
        if "/event/" in path:
            path += "enceventid?access_token=arbitrarytoken"
            return call(nio.RoomGetEventResponse, method, path)
        else:
            path = path.rstrip("/")
            path += "?access_token=arbitrarytoken"
            return call(
                nio.RoomGetStateEventResponse,
                method,
                path,
                response_data=("dev.opsdroid.database", f"{state_key}", "!notaroomid"),
            )
    elif "/send" in path:
        path += "bigrandomuuid?access_token=arbitrarytoken"
        return call(
            nio.RoomSendResponse,
            method,
            path,
            JSONEncoder(separators=(",", ":")).encode(content),
            ("!notaroomid",),
        )
    else:
        path = path.rstrip("/")
        path += "?access_token=arbitrarytoken"
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
    patched_send.return_value.transport_response = AsyncMock()
    patched_send.return_value.transport_response.status = 404

    db = DatabaseMatrix({"should_encrypt": False}, opsdroid=opsdroid_matrix)
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
        ]
    )


@pytest.mark.asyncio
@pytest.mark.xfail(
    not nio.crypto.ENCRYPTION_ENABLED, reason="No encryption deps installed for matrix"
)
async def test_default_config_enc(patched_send, opsdroid_matrix, patched_uuid):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse({}, "", "", "")
            resp.transport_response = AsyncMock()
            resp.transport_response.status = 404
            return resp
        else:
            return nio.RoomSendResponse("enceventid", "!notaroomid")

    patched_send.side_effect = side_effect

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
                "/_matrix/client/r0/rooms/%21notaroomid/send/dev.opsdroid.database/",
                {"twim": {"hello": "world"}},
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
async def test_put_custom_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse({}, "", "", "")
    patched_send.return_value.transport_response = AsyncMock()
    patched_send.return_value.transport_response.status = 404

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": "wibble"},
        opsdroid=opsdroid_matrix,
    )
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
        ]
    )


@pytest.mark.asyncio
@pytest.mark.xfail(
    not nio.crypto.ENCRYPTION_ENABLED, reason="No encryption deps installed for matrix"
)
async def test_put_custom_state_key_enc(patched_send, opsdroid_matrix, patched_uuid):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse({}, "", "", "")
            resp.transport_response = AsyncMock()
            resp.transport_response.status = 404
            return resp
        else:
            return nio.RoomSendResponse("enceventid", "!notaroomid")

    patched_send.side_effect = side_effect

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
                "/_matrix/client/r0/rooms/%21notaroomid/send/dev.opsdroid.database/",
                {"twim": {"hello": "world"}},
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/wibble",
                {"twim": {"encrypted_val": "enceventid"}},
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_single_state_key_false(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse({}, "", "", "")
    patched_send.return_value.transport_response = AsyncMock()
    patched_send.return_value.transport_response.status = 404

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": False}, opsdroid=opsdroid_matrix
    )
    db.should_migrate = False
    await db.put("hello", "world")

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/hello",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/hello",
                {"hello": "world"},
            ),
        ]
    )


@pytest.mark.asyncio
@pytest.mark.xfail(
    not nio.crypto.ENCRYPTION_ENABLED, reason="No encryption deps installed for matrix"
)
async def test_single_state_key_false_enc(patched_send, opsdroid_matrix, patched_uuid):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse({}, "", "", "")
            resp.transport_response = AsyncMock()
            resp.transport_response.status = 404
            return resp
        else:
            return nio.RoomSendResponse("enceventid", "!notaroomid")

    patched_send.side_effect = side_effect

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("hello", "world")

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/hello",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/send/dev.opsdroid.database/",
                {"hello": "world"},
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/hello",
                {"hello": {"encrypted_val": "enceventid"}},
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_single_state_key_false_dict(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse({}, "", "", "")
    patched_send.return_value.transport_response = AsyncMock()
    patched_send.return_value.transport_response.status = 404

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": False}, opsdroid=opsdroid_matrix
    )
    db.should_migrate = False
    await db.put("twim", {"hello": "world", "twim": "hello"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
                {"twim": {"hello": "world", "twim": "hello"}},
            ),
        ]
    )


@pytest.mark.asyncio
@pytest.mark.xfail(
    not nio.crypto.ENCRYPTION_ENABLED, reason="No encryption deps installed for matrix"
)
async def test_single_state_key_false_dict_enc(
    patched_send, opsdroid_matrix, patched_uuid
):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse({}, "", "", "")
            resp.transport_response = AsyncMock()
            resp.transport_response.status = 404
            return resp
        else:
            return nio.RoomSendResponse("enceventid", "!notaroomid")

    patched_send.side_effect = side_effect

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", {"hello": "world", "twim": "hello"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/send/dev.opsdroid.database/",
                {"twim": {"hello": "world", "twim": "hello"}},
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
                {"twim": {"encrypted_val": "enceventid"}},
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_single_state_not_a_dict(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse({}, "", "", "")
    patched_send.return_value.transport_response = AsyncMock()
    patched_send.return_value.transport_response.status = 404

    value = "world"
    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": True}, opsdroid=opsdroid_matrix
    )
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
        ]
    )


@pytest.mark.asyncio
async def test_default_update_same_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": {"hello": "world"}}, "", "", ""
    )

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": False}, opsdroid=opsdroid_matrix
    )
    db.should_migrate = False

    await db.put("twim", {"hello": "bob"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
                {"twim": {"hello": "bob"}},
            ),
        ]
    )


@pytest.mark.asyncio
@pytest.mark.xfail(
    not nio.crypto.ENCRYPTION_ENABLED, reason="No encryption deps installed for matrix"
)
async def test_default_update_same_key_enc(patched_send, opsdroid_matrix, patched_uuid):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse(
                {"twim": {"encrypted_val": "enceventid"}}, "", "", ""
            )
            return resp
        elif resp is nio.RoomGetEventResponse:
            event = nio.Event(
                {
                    "type": "dev.opsdroid.database",
                    "event_id": "enceventid",
                    "sender": "@someone:localhost",
                    "origin_server_ts": "2005",
                    "content": {"twim": {"hello": "world"}},
                }
            )
            resp = nio.RoomGetEventResponse()
            resp.event = event
            return resp
        else:
            return nio.RoomSendResponse("enceventid", "!notaroomid")

    patched_send.side_effect = side_effect

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", {"hello": "bob"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            ),
            matrix_call("GET", "/_matrix/client/r0/rooms/%21notaroomid/event/"),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/send/dev.opsdroid.database/",
                {"twim": {"hello": "bob"}},
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
                {"twim": {"encrypted_val": "enceventid"}},
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_update_same_key_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": {"hello": "world"}}, "", "", ""
    )

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": True}, opsdroid=opsdroid_matrix
    )
    db.should_migrate = False

    await db.put("twim", {"hello": "bob"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
                {"twim": {"hello": "bob"}},
            ),
        ]
    )


@pytest.mark.asyncio
@pytest.mark.xfail(
    not nio.crypto.ENCRYPTION_ENABLED, reason="No encryption deps installed for matrix"
)
async def test_update_same_key_single_state_key_enc(
    patched_send, opsdroid_matrix, patched_uuid
):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse(
                {"twim": {"encrypted_val": "enceventid"}}, "", "", ""
            )
            return resp
        elif resp is nio.RoomGetEventResponse:
            event = nio.Event(
                {
                    "type": "dev.opsdroid.database",
                    "event_id": "enceventid",
                    "sender": "@someone:localhost",
                    "origin_server_ts": "2005",
                    "content": {"twim": {"hello": "world"}},
                }
            )
            resp = nio.RoomGetEventResponse()
            resp.event = event
            return resp
        else:
            return nio.RoomSendResponse("enceventid", "!notaroomid")

    patched_send.side_effect = side_effect

    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", {"hello": "bob"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            ),
            matrix_call("GET", "/_matrix/client/r0/rooms/%21notaroomid/event/"),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/send/dev.opsdroid.database/",
                {"twim": {"hello": "bob"}},
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
async def test_default_update_same_key_value(patched_send, opsdroid_matrix, caplog):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": {"hello": "world"}}, "", "", ""
    )

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": False}, opsdroid=opsdroid_matrix
    )
    db.should_migrate = False
    caplog.clear()
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            )
        ]
    )

    assert ["Not updating matrix state, as content hasn't changed."] == [
        rec.message for rec in caplog.records
    ]


# This will pass even without enc since we dont get to the part in put where that's relevant
@pytest.mark.asyncio
async def test_default_update_same_key_value_enc(
    patched_send, opsdroid_matrix, patched_uuid, caplog
):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse(
                {"twim": {"encrypted_val": "enceventid"}}, "", "", ""
            )
            return resp
        else:
            event = nio.Event(
                {
                    "type": "dev.opsdroid.database",
                    "event_id": "enceventid",
                    "sender": "@someone:localhost",
                    "origin_server_ts": "2005",
                    "content": {"twim": {"hello": "world"}},
                }
            )
            resp = nio.RoomGetEventResponse()
            resp.event = event
            return resp

    patched_send.side_effect = side_effect

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    caplog.clear()
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            ),
            matrix_call("GET", "/_matrix/client/r0/rooms/%21notaroomid/event/"),
        ]
    )

    assert ["Not updating matrix state, as content hasn't changed."] == [
        rec.message for rec in caplog.records
    ]


@pytest.mark.asyncio
async def test_default_update_same_key_value_single_state_key(
    patched_send, opsdroid_matrix, caplog
):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": {"hello": "world"}}, "", "", ""
    )

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": True}, opsdroid=opsdroid_matrix
    )
    db.should_migrate = False
    caplog.clear()
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            )
        ]
    )

    assert ["Not updating matrix state, as content hasn't changed."] == [
        rec.message for rec in caplog.records
    ]


# This will pass even without enc since we dont get to the part in put where that's relevant
@pytest.mark.asyncio
async def test_default_update_same_key_value_single_state_key_enc(
    patched_send, opsdroid_matrix, patched_uuid, caplog
):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse(
                {"twim": {"encrypted_val": "enceventid"}}, "", "", ""
            )
            return resp
        else:
            event = nio.Event(
                {
                    "type": "dev.opsdroid.database",
                    "event_id": "enceventid",
                    "sender": "@someone:localhost",
                    "origin_server_ts": "2005",
                    "content": {"twim": {"hello": "world"}},
                }
            )
            resp = nio.RoomGetEventResponse()
            resp.event = event
            return resp

    patched_send.side_effect = side_effect

    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    caplog.clear()
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            ),
            matrix_call("GET", "/_matrix/client/r0/rooms/%21notaroomid/event/"),
        ]
    )

    assert ["Not updating matrix state, as content hasn't changed."] == [
        rec.message for rec in caplog.records
    ]


@pytest.mark.asyncio
async def test_default_update_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": "hello"}, "", "", ""
    )

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": True}, opsdroid=opsdroid_matrix
    )
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
        ]
    )


@pytest.mark.asyncio
@pytest.mark.xfail(
    not nio.crypto.ENCRYPTION_ENABLED, reason="No encryption deps installed for matrix"
)
async def test_default_update_single_state_key_enc(
    patched_send, opsdroid_matrix, patched_uuid
):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse({"twim": "hello"}, "", "", "")
            return resp
        else:
            return nio.RoomSendResponse("enceventid", "!notaroomid")

    patched_send.side_effect = side_effect

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
                "/_matrix/client/r0/rooms/%21notaroomid/send/dev.opsdroid.database/",
                {"pill": "red"},
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
                {"twim": "hello", "pill": {"encrypted_val": "enceventid"}},
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_get_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": "hello", "wibble": "wobble"}, "", "", ""
    )

    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get("twim")

    patched_send.assert_called_once_with(
        nio.RoomGetStateEventResponse,
        "GET",
        "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database?access_token=arbitrarytoken",
        response_data=("dev.opsdroid.database", "", "!notaroomid"),
    )

    assert data == "hello"


@pytest.mark.asyncio
async def test_get_single_state_key_enc(patched_send, opsdroid_matrix):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse(
                {"twim": {"encrypted_val": "enceventid"}, "wibble": "wobble"},
                "",
                "",
                "",
            )
            return resp
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
            matrix_call("GET", "/_matrix/client/r0/rooms/%21notaroomid/event/"),
        ]
    )

    assert data == "hello"


@pytest.mark.asyncio
async def test_get(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": "world"}, "", "", ""
    )

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": False}, opsdroid=opsdroid_matrix
    )
    db.should_migrate = False

    data = await db.get("twim")

    patched_send.assert_called_once_with(
        nio.RoomGetStateEventResponse,
        "GET",
        "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim?access_token=arbitrarytoken",
        response_data=("dev.opsdroid.database", "twim", "!notaroomid"),
    )

    assert data == "world"


@pytest.mark.asyncio
async def test_get_enc(patched_send, opsdroid_matrix):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse(
                {"twim": {"encrypted_val": "enceventid"}}, "", "", ""
            )
            return resp
        else:
            event = nio.Event(
                {
                    "type": "dev.opsdroid.database",
                    "event_id": "enceventid",
                    "sender": "@someone:localhost",
                    "origin_server_ts": "2005",
                    "content": {"twim": "world"},
                }
            )
            resp = nio.RoomGetEventResponse()
            resp.event = event
            return resp

    patched_send.side_effect = side_effect

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    data = await db.get("twim")

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            ),
            matrix_call("GET", "/_matrix/client/r0/rooms/%21notaroomid/event/"),
        ]
    )

    assert data == "world"


@pytest.mark.asyncio
async def test_get_no_key_single_state_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"wibble": "wobble"}, "", "", ""
    )

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": True}, opsdroid=opsdroid_matrix
    )
    db.should_migrate = False

    data = await db.get("twim")

    assert data is None


@pytest.mark.asyncio
async def test_get_no_key_404(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventError({"errcode": "M_NOTFOUND"})
    patched_send.return_value.transport_response = AsyncMock()
    patched_send.return_value.transport_response.status = 404

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": False}, opsdroid=opsdroid_matrix
    )
    db.should_migrate = False

    data = await db.get("twim")
    assert data is None


@pytest.mark.asyncio
async def test_get_no_key_500(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventError({"code": 500})

    db = DatabaseMatrix(
        {"should_encrypt": False, "single_state_key": False}, opsdroid=opsdroid_matrix
    )
    db.should_migrate = False

    with pytest.raises(RuntimeError):
        await db.get("twim")


@pytest.mark.asyncio
async def test_delete(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": "hello"}, "", "", ""
    )

    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    data = await db.delete("twim")

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
                {},
            ),
        ]
    )

    assert data == "hello"


@pytest.mark.asyncio
async def test_delete_single_state_key_false(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": "hello"}, "", "", ""
    )

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    data = await db.delete("twim")

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
                {},
            ),
        ]
    )

    assert data == "hello"


@pytest.mark.asyncio
async def test_get_empty(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse({}, "", "", "")

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    assert await db.get("test") is None


@pytest.mark.asyncio
async def test_delete_multiple_keys(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"hello": "world", "twim": "hello", "pill": "red"}, "", "", ""
    )

    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    data = await db.delete(["hello", "twim"])

    patched_send.assert_has_calls(
        [
            matrix_call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
            ),
            matrix_call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/",
                {"pill": "red"},
            ),
        ]
    )

    assert data == ["world", "hello"]


@pytest.mark.asyncio
async def test_delete_no_key(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"twim": "hello"}, "", "", ""
    )

    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    data = await db.delete("pill")

    assert data is None


@pytest.mark.asyncio
async def test_delete_no_key_single_state_key_false(
    patched_send, opsdroid_matrix, caplog
):
    patched_send.return_value = nio.RoomGetStateEventResponse({}, "", "", "")
    patched_send.return_value.transport_response = AsyncMock()
    patched_send.return_value.transport_response.status = 404

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    caplog.clear()
    data = await db.delete("twim")

    assert data is None

    assert [
        "State event dev.opsdroid.database with state key 'twim' doesn't exist."
    ] == [rec.message for rec in caplog.records]


@pytest.mark.asyncio
async def test_connect(patched_send, opsdroid_matrix):
    db = DatabaseMatrix({"should_encrypt": False}, opsdroid=opsdroid_matrix)

    await db.connect()


@pytest.mark.asyncio
async def test_room_switch(patched_send, opsdroid_matrix):
    patched_send.return_value = nio.RoomGetStateEventResponse(
        {"hello": "world"}, "", "", ""
    )

    db = DatabaseMatrix({"should_encrypt": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    with db.memory_in_room("!notanotherroom"):
        assert db.room == "!notanotherroom"
        data = await db.get("hello")

    patched_send.assert_called_once_with(
        nio.RoomGetStateEventResponse,
        "GET",
        "/_matrix/client/r0/rooms/%21notanotherroom/state/dev.opsdroid.database?access_token=arbitrarytoken",
        response_data=("dev.opsdroid.database", "", "!notanotherroom"),
    )

    assert db.room == "main"
    assert data == "world"


@pytest.mark.asyncio
async def test_decorator(opsdroid_matrix):

    db = DatabaseMatrix({"should_encrypt": False}, opsdroid=opsdroid_matrix)
    opsdroid_matrix.memory.databases.append(db)

    @memory_in_event_room
    async def skill_func(opsdroid, config, message):
        database = opsdroid.get_database("matrix")
        return database.room

    msg = Message("", target="!notanotherroom")

    ret_room = await skill_func(opsdroid_matrix, opsdroid_matrix.config, msg)

    assert ret_room == "!notanotherroom"


@pytest.mark.asyncio
async def test_decorator_no_db(opsdroid_matrix):
    @memory_in_event_room
    async def skill_func(opsdroid, config, message):
        database = opsdroid.get_database("matrix")
        return database

    msg = Message("", target="!notanotherroom")

    ret_db = await skill_func(opsdroid_matrix, opsdroid_matrix.config, msg)

    assert ret_db is None


@pytest.mark.asyncio
async def test_migrate(patched_send, opsdroid_matrix, mocker, caplog, patched_uuid):
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
        elif resp is nio.RoomPutStateResponse:
            return resp
        else:
            return nio.RoomGetStateEventError(message="testing")

    patched_send.side_effect = side_effect

    db = DatabaseMatrix({"should_encrypt": False}, opsdroid=opsdroid_matrix)
    with pytest.raises(RuntimeError):
        await db.put("hello", "bob")

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
        ]
    )


# @pytest.mark.skip("intermittent failures")
@pytest.mark.asyncio
async def test_migrate_single_state_key_false(
    patched_send, opsdroid_matrix, mocker, caplog, patched_uuid
):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateResponse:
            return nio.RoomGetStateResponse(
                [
                    {
                        "type": "opsdroid.database",
                        "state_key": "twim",
                        "event_id": "roomeventid",
                        "content": {"hello": "world"},
                    }
                ],
                "!notaroomid",
            )
        elif resp is nio.RoomPutStateResponse:
            return resp
        else:
            return nio.RoomGetStateEventError(message="testing")

    patched_send.side_effect = side_effect

    db = DatabaseMatrix(
        {"single_state_key": False, "should_encrypt": False}, opsdroid=opsdroid_matrix
    )
    with pytest.raises(RuntimeError):
        await db.put("twim", "bob")

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
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim",
                {"twim": {"hello": "world"}},
            ),
            call(
                nio.RoomRedactResponse,
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/redact/roomeventid/bigrandomuuid?access_token=arbitrarytoken",
                "{}",
                response_data=("!notaroomid",),
            ),
        ]
    )


@pytest.mark.asyncio
async def test_errors(patched_send, opsdroid_matrix, mocker, caplog, patched_uuid):
    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse(
                {"twim": {"encrypted_val": "enceventid"}}, "", "", ""
            )
            return resp
        else:
            return nio.RoomGetEventError(message="testing")

    patched_send.side_effect = side_effect

    db = DatabaseMatrix({"should_encrypt": False}, opsdroid=opsdroid_matrix)
    caplog.clear()
    db.should_migrate = False
    await db.get("twim")

    assert ["Error decrypting event enceventid while getting twim: testing(None)"] == [
        rec.message for rec in caplog.records
    ]

    patched_send.side_effect = [
        nio.RoomGetStateError(message="testing"),
        nio.RoomGetStateEventError(message="testing"),
    ]
    caplog.clear()
    db.should_migrate = True
    with pytest.raises(RuntimeError):
        await db.get("hello")

    assert [
        "Error migrating from opsdroid.database to dev.opsdroid.database in room !notaroomid: testing(None)"
    ] == [rec.message for rec in caplog.records]

    patched_send.side_effect = [
        nio.RoomGetStateError(message="testing"),
        nio.RoomGetStateEventError(message="testing"),
    ]
    caplog.clear()
    db.should_migrate = True
    await db.delete("hello")

    assert [
        "Error migrating from opsdroid.database to dev.opsdroid.database in room !notaroomid: testing(None)",
        "Error deleting hello from matrix room !notaroomid: testing(None)",
    ] == [rec.message for rec in caplog.records]

    def side_effect(resp, *args, **kwargs):
        if resp is nio.RoomGetStateEventResponse:
            resp = nio.RoomGetStateEventResponse(
                {"hello": {"encrypted_val": "enceventid"}}, "", "", ""
            )
            return resp
        else:
            return nio.RoomGetEventError(message="testing")

    patched_send.side_effect = side_effect

    caplog.clear()
    db.connector._allow_encryption = True
    db.should_migrate = False
    db._single_state_key = False
    with pytest.raises(MatrixException):
        await db.put("twim", {"hello": "world"})

    assert ["Error decrypting event enceventid while getting twim: testing(None)"] == [
        rec.message for rec in caplog.records
    ]

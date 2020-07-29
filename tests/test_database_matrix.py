from unittest.mock import call

import pytest
import nio

from opsdroid.connector.matrix import ConnectorMatrix
from opsdroid.core import OpsDroid
from opsdroid.database.matrix import DatabaseMatrix


@pytest.fixture
def patched_send(mocker):
    return mocker.patch("nio.AsyncClient.send")


@pytest.fixture
def patched_response(mocker):
    return mocker.patch("nio.AsyncClient.create_matrix_response")


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


@pytest.mark.asyncio
async def test_default_config(patched_send, opsdroid_matrix, patched_response):
    patched_response.return_value = nio.RoomGetStateEventResponse({}, "", "", "")

    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/?access_token=arbitrarytoken",
                None,
                {"Content-Type": "application/json"},
                None,
                None,
            ),
            call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/?access_token=arbitrarytoken",
                '{"twim":{"hello":"world"}}',
                {"Content-Type": "application/json"},
                None,
                None,
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_put_custom_state_key(patched_send, opsdroid_matrix, patched_response):
    patched_response.return_value = nio.RoomGetStateEventResponse({}, "", "", "")

    db = DatabaseMatrix({"single_state_key": "wibble"}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/wibble?access_token=arbitrarytoken",
                None,
                {"Content-Type": "application/json"},
                None,
                None,
            ),
            call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/wibble?access_token=arbitrarytoken",
                '{"twim":{"hello":"world"}}',
                {"Content-Type": "application/json"},
                None,
                None,
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_single_state_key_false(patched_send, opsdroid_matrix, patched_response):
    patched_response.return_value = nio.RoomGetStateEventResponse({}, "", "", "")

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", {"hello": "world"})

    patched_send.assert_has_calls(
        [
            call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim?access_token=arbitrarytoken",
                None,
                {"Content-Type": "application/json"},
                None,
                None,
            ),
            call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim?access_token=arbitrarytoken",
                '{"hello":"world"}',
                {"Content-Type": "application/json"},
                None,
                None,
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_single_state_not_a_dict(patched_send, opsdroid_matrix, patched_response):
    patched_response.return_value = nio.RoomGetStateEventResponse({}, "", "", "")

    value = "world"
    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False
    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/?access_token=arbitrarytoken",
                None,
                {"Content-Type": "application/json"},
                None,
                None,
            ),
            call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/?access_token=arbitrarytoken",
                '{"twim":"world"}',
                {"Content-Type": "application/json"},
                None,
                None,
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_default_not_a_dict(patched_send, opsdroid_matrix, patched_response):
    patched_response.return_value = nio.RoomGetStateEventResponse({}, "", "", "")

    value = "world"
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    with pytest.raises(ValueError):
        await db.put("twim", value)


@pytest.mark.asyncio
async def test_default_update_different_value(
    patched_send, opsdroid_matrix, patched_response
):
    patched_response.return_value = nio.RoomGetStateEventResponse(
        {"hello": "world"}, "", "", ""
    )

    value = {"red": "pill"}
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim?access_token=arbitrarytoken",
                None,
                {"Content-Type": "application/json"},
                None,
                None,
            ),
            call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim?access_token=arbitrarytoken",
                '{"hello":"world","red":"pill"}',
                {"Content-Type": "application/json"},
                None,
                None,
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_default_update_same_key(patched_send, opsdroid_matrix, patched_response):
    patched_response.return_value = nio.RoomGetStateEventResponse(
        {"hello": "world"}, "", "", ""
    )

    value = {"hello": "bob"}
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim?access_token=arbitrarytoken",
                None,
                {"Content-Type": "application/json"},
                None,
                None,
            ),
            call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim?access_token=arbitrarytoken",
                '{"hello":"bob"}',
                {"Content-Type": "application/json"},
                None,
                None,
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_update_same_key_single_state_key(
    patched_send, opsdroid_matrix, patched_response
):
    patched_response.return_value = nio.RoomGetStateEventResponse(
        {"twim": {"hello": "world"}}, "", "", ""
    )

    value = {"hello": "bob"}
    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/?access_token=arbitrarytoken",
                None,
                {"Content-Type": "application/json"},
                None,
                None,
            ),
            call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/?access_token=arbitrarytoken",
                '{"twim":{"hello":"bob"}}',
                {"Content-Type": "application/json"},
                None,
                None,
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_default_update_same_key_value(
    patched_send, opsdroid_matrix, patched_response
):
    patched_response.return_value = nio.RoomGetStateEventResponse(
        {"hello": "world"}, "", "", ""
    )

    value = {"hello": "world"}
    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim?access_token=arbitrarytoken",
                None,
                {"Content-Type": "application/json"},
                None,
                None,
            )
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_default_update_same_key_value_single_state_key(
    patched_send, opsdroid_matrix, patched_response
):
    patched_response.return_value = nio.RoomGetStateEventResponse(
        {"twim": {"hello": "world"}}, "", "", ""
    )

    value = {"hello": "world"}
    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("twim", value)

    patched_send.assert_has_calls(
        [
            call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/?access_token=arbitrarytoken",
                None,
                {"Content-Type": "application/json"},
                None,
                None,
            )
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_default_update_single_state_key(
    patched_send, opsdroid_matrix, patched_response
):
    patched_response.return_value = nio.RoomGetStateEventResponse(
        {"twim": "hello"}, "", "", ""
    )

    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    await db.put("pill", "red")

    patched_send.assert_has_calls(
        [
            call(
                "GET",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/?access_token=arbitrarytoken",
                None,
                {"Content-Type": "application/json"},
                None,
                None,
            ),
            call(
                "PUT",
                "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/?access_token=arbitrarytoken",
                '{"twim":"hello","pill":"red"}',
                {"Content-Type": "application/json"},
                None,
                None,
            ),
        ],
        any_order=True,
    )


@pytest.mark.asyncio
async def test_get_single_state_key(patched_send, opsdroid_matrix, patched_response):
    patched_response.return_value = nio.RoomGetStateEventResponse(
        {"twim": "hello", "wibble": "wobble"}, "", "", ""
    )

    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get("twim")

    patched_send.assert_called_once_with(
        "GET",
        "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/?access_token=arbitrarytoken",
        None,
        {"Content-Type": "application/json"},
        None,
        None,
    )

    assert data == "hello"


@pytest.mark.asyncio
async def test_get(patched_send, opsdroid_matrix, patched_response):
    patched_response.return_value = nio.RoomGetStateEventResponse(
        {"hello": "world"}, "", "", ""
    )

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get({"twim": "hello"})

    patched_send.assert_called_once_with(
        "GET",
        "/_matrix/client/r0/rooms/%21notaroomid/state/dev.opsdroid.database/twim?access_token=arbitrarytoken",
        None,
        {"Content-Type": "application/json"},
        None,
        None,
    )

    assert data == "world"


@pytest.mark.asyncio
async def test_get_no_key_single_state_key(
    patched_send, opsdroid_matrix, patched_response
):
    patched_response.return_value = nio.RoomGetStateEventResponse(
        {"wibble": "wobble"}, "", "", ""
    )

    db = DatabaseMatrix({"single_state_key": True}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get("twim")

    assert data is None


@pytest.mark.asyncio
async def test_get_no_key_404(patched_send, opsdroid_matrix, patched_response):
    patched_response.return_value = nio.RoomGetStateEventError({"errcode": 404})

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get("twim")

    assert data is None


@pytest.mark.asyncio
async def test_get_no_key_500(patched_send, opsdroid_matrix, patched_response):
    patched_response.return_value = nio.RoomGetStateEventError({"code": 500})

    db = DatabaseMatrix({"single_state_key": False}, opsdroid=opsdroid_matrix)
    db.should_migrate = False

    data = await db.get("twim")

    assert data is None


@pytest.mark.asyncio
async def test_connect(patched_send, opsdroid_matrix):
    db = DatabaseMatrix({}, opsdroid=opsdroid_matrix)

    await db.connect()

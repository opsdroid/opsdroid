import json
from pathlib import Path

import pytest
import nio

from opsdroid.connector.matrix import ConnectorMatrix

################################################################################
# Connector and config fixtures.
################################################################################


@pytest.fixture
def default_config(mock_api_obj):
    return {"homeserver": mock_api_obj.base_url, "rooms": {"main": "#test:localhost"}}


@pytest.fixture
def login_config(mock_api_obj):
    return {
        "mxid": "@opsdroid:localhost",
        "password": "supersecret",
        "homeserver": mock_api_obj.base_url,
        "rooms": {"main": "#test:localhost"},
    }


@pytest.fixture
def token_config(mock_api_obj):
    return {
        "access_token": "token",
        "homeserver": mock_api_obj.base_url,
        "rooms": {"main": "#test:localhost"},
    }


@pytest.fixture
async def connector(opsdroid, request, mock_api_obj, mocker):
    if hasattr(request, "param"):
        fix_name = request.param
    else:
        marker = request.node.get_closest_marker("matrix_connector_config")
        fix_name = marker.args[0]

    if isinstance(fix_name, str):
        config = request.getfixturevalue(fix_name)
    elif isinstance(fix_name, dict):
        config = fix_name
    else:
        raise TypeError(
            "Config should be a string name for a fixture or a dict for the config"
        )

    if "homeserver" not in config:
        config["homeserver"] = mock_api_obj.base_url

    conn = ConnectorMatrix(config, opsdroid=opsdroid)
    conn.connection = mocker.MagicMock()
    yield conn
    if isinstance(conn.connection, nio.AsyncClient):
        await conn.disconnect()


@pytest.fixture
async def connector_connected(
    opsdroid,
    double_filter_response,
    single_message_sync_response,
    mock_whoami_join,
    mock_api,
):
    config = {
        "access_token": "token",
        "homeserver": mock_api.base_url,
        "rooms": {"main": "#test:localhost"},
    }
    conn = ConnectorMatrix(config, opsdroid=opsdroid)
    await conn.connect()
    yield conn
    await conn.disconnect()


################################################################################
# Sync Factory
################################################################################


def get_matrix_response(name):
    return Path(__file__).parent / "responses" / f"{name}.json"


def empty_sync(room_id):
    with open(get_matrix_response("empty_sync_response")) as fobj:
        empty_sync = json.load(fobj)

    room_block = empty_sync["rooms"]["join"].pop("ROOMID")
    empty_sync["rooms"]["join"][room_id] = room_block

    return empty_sync


def event_factory(event_type, content, sender):
    return {
        "content": content,
        "event_id": "$1234567890987654321234567890",
        "origin_server_ts": 9876543210,
        "sender": sender,
        "type": event_type,
        "unsigned": {"age": 100},
    }


def message_factory(body, msgtype, sender, **extra_content):
    content = {"msgtype": msgtype, "body": body, **extra_content}
    return event_factory("m.room.message", content, sender)


def sync_response(events, room_id="!12345:localhost"):
    sync = empty_sync(room_id)
    sync["rooms"]["join"][room_id]["timeline"]["events"] = events
    return sync


@pytest.fixture
def message_sync_response(request):
    room_id = "!12345:localhost"
    room_id_markers = [
        marker for marker in request.node.own_markers if marker.name == "sync_room_id"
    ]
    if room_id:
        room_id = room_id_markers[0].args[0]

    markers = [
        marker
        for marker in request.node.own_markers
        if marker.name == "add_sync_messsage"
    ]

    events = []
    for marker in markers:
        events.append(message_factory(*marker.args, **marker.kwargs))

    return sync_response(events, room_id=room_id)


################################################################################
# Response Fixtures
################################################################################


@pytest.fixture
def double_filter_response(mock_api_obj):
    mock_api_obj.add_response(
        "/_matrix/client/r0/user/@opsdroid:localhost/filter",
        "POST",
        {"filter_id": "1234567890"},
    )
    mock_api_obj.add_response(
        "/_matrix/client/r0/user/@opsdroid:localhost/filter",
        "POST",
        {"filter_id": "0987654321"},
    )


@pytest.fixture
def single_message_sync_response(mock_api_obj):
    """Return a sync response with a single test message in it."""
    event = message_factory("Test", "m.text", "@stuart:localhost")
    sync = sync_response([event])
    mock_api_obj.add_response("/_matrix/client/r0/sync", "GET", sync)


@pytest.fixture
def mock_whoami_join(mock_api_obj):
    mock_api_obj.add_response(
        "/_matrix/client/r0/account/whoami", "GET", {"user_id": "@opsdroid:localhost"}
    )
    mock_api_obj.add_response(
        "/_matrix/client/r0/join/#test:localhost",
        "POST",
        {"room_id": "!12355:localhost"},
    )

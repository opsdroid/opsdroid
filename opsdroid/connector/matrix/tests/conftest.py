from pathlib import Path

import pytest

from opsdroid.connector.matrix import ConnectorMatrix

################################################################################
# Connector and config fixtures.
################################################################################


@pytest.fixture
def default_config(mock_api_obj):
    return {
        "homeserver": mock_api_obj.base_url,
        "rooms": {"main": "#test:localhost"},
    }


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
async def connector(opsdroid, request):
    if hasattr(request, "param"):
        fix_name = request.param
    else:
        marker = request.node.get_closest_marker("matrix_connector_config")
        fix_name = marker.args[0]

    config = request.getfixturevalue(fix_name)

    conn = ConnectorMatrix(config, opsdroid=opsdroid)
    yield conn
    if conn.connection is not None:
        await conn.disconnect()


################################################################################
# Sync Factory
################################################################################


def get_matrix_response(name):
    return Path(__file__).parent / "responses" / f"{name}.json"


def empty_sync(room_id):
    with open(get_matrix_response("empty_sync_response")) as fobj:
        empty_sync = json.load(fobj.read())

    room_block = empty_sync["rooms"]["join"].pop("ROOMID")
    empty_sync["rooms"]["join"][room_id] = room_block


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
    mock_api_obj.add_response(
        "/_matrix/client/r0/sync", "GET", get_matrix_response("single_message_sync")
    )

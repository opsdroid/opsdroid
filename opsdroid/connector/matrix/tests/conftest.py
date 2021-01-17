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
# Response Fixtures
################################################################################


def get_matrix_response(name):
    return Path(__file__).parent / "responses" / f"{name}.json"


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

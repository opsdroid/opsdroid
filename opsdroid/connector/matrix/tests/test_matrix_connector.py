import pytest

from opsdroid.connector.matrix import ConnectorMatrix


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
def connector(opsdroid, request):
    if hasattr(request, "param"):
        fix_name = request.param
    else:
        marker = request.node.get_closest_marker("matrix_connector_config")
        fix_name = marker.args[0]

    config = request.getfixturevalue(fix_name)

    return ConnectorMatrix(config, opsdroid=opsdroid)


def test_constructor(opsdroid, default_config):
    connector = ConnectorMatrix(default_config, opsdroid)
    assert isinstance(connector, ConnectorMatrix)


filter_args = (
    "/_matrix/client/r0/user/@opsdroid:localhost/filter",
    "POST",
    {"filter_id": "928409384"},
)


@pytest.mark.matrix_connector_config("token_config")
@pytest.mark.add_response(
    "/_matrix/client/r0/account/whoami", "GET", {"user_id": "@opsdroid:localhost"}
)
@pytest.mark.add_response(*filter_args)
@pytest.mark.add_response(*filter_args)
# This is an invalid sync response, but it doesn't matter
@pytest.mark.add_response("/_matrix/client/r0/sync", "GET", {})
@pytest.mark.add_response(
    "/_matrix/client/r0/join/#test:localhost", "POST", {"room_id": "!12355:localhost"}
)
@pytest.mark.asyncio
async def test_connect_access_token(opsdroid, connector, mock_api):
    assert isinstance(connector, ConnectorMatrix)
    assert connector.access_token == "token"
    await connector.connect()

    assert mock_api.called("/_matrix/client/r0/account/whoami")
    assert (
        mock_api.call_count("/_matrix/client/r0/user/@opsdroid:localhost/filter") == 2
    )
    assert mock_api.called("/_matrix/client/r0/sync")
    assert mock_api.called("/_matrix/client/r0/join/#test:localhost")

    whoami_call = mock_api.get_request("/_matrix/client/r0/account/whoami", 0)
    assert "access_token" in whoami_call.query
    assert whoami_call.query["access_token"] == "token"


@pytest.mark.matrix_connector_config("login_config")
@pytest.mark.add_response(
    "/_matrix/client/r0/login",
    "POST",
    {
        "user_id": "@opsdroid:localhost",
        "access_token": "abc123",
        "device_id": "GHTYAJCE",
    },
)
@pytest.mark.add_response(*filter_args)
@pytest.mark.add_response(*filter_args)
# This is an invalid sync response, but it doesn't matter
@pytest.mark.add_response("/_matrix/client/r0/sync", "GET", {})
@pytest.mark.add_response(
    "/_matrix/client/r0/join/#test:localhost", "POST", {"room_id": "!12355:localhost"}
)
@pytest.mark.asyncio
async def test_connect_login(opsdroid, connector, mock_api):
    assert isinstance(connector, ConnectorMatrix)
    await connector.connect()

    assert mock_api.called("/_matrix/client/r0/login")
    assert (
        mock_api.call_count("/_matrix/client/r0/user/@opsdroid:localhost/filter") == 2
    )
    assert mock_api.called("/_matrix/client/r0/sync")
    assert mock_api.called("/_matrix/client/r0/join/#test:localhost")

    assert connector.access_token == connector.connection.access_token == "abc123"

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


@pytest.mark.matrix_connector_config("token_config")
@pytest.mark.add_response(
    "/_matrix/client/r0/account/whoami", "GET", {"user_id": "@neo:matrix.org"}
)
@pytest.mark.asyncio
async def test_connect_access_token(opsdroid, connector, mock_api):
    assert isinstance(connector, ConnectorMatrix)
    await connector.connect()

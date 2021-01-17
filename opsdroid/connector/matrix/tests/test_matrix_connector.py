import pytest

from opsdroid.connector.matrix import ConnectorMatrix


def test_constructor(opsdroid, default_config):
    connector = ConnectorMatrix(default_config, opsdroid)
    assert isinstance(connector, ConnectorMatrix)


@pytest.mark.matrix_connector_config("token_config")
@pytest.mark.add_response(
    "/_matrix/client/r0/account/whoami", "GET", {"user_id": "@opsdroid:localhost"}
)
@pytest.mark.add_response(
    "/_matrix/client/r0/join/#test:localhost", "POST", {"room_id": "!12355:localhost"}
)
@pytest.mark.asyncio
async def test_connect_access_token(
    opsdroid, connector, double_filter_response, single_message_sync_response, mock_api
):
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


@pytest.mark.matrix_connector_config("token_config")
@pytest.mark.add_response(
    "/_matrix/client/r0/account/whoami",
    "GET",
    {
        "errcode": "M_UNKNOWN_TOKEN",
        "error": "Invalid macaroon passed.",
    },
    status=401,
)
@pytest.mark.asyncio
async def test_connect_invalid_access_token(caplog, opsdroid, connector, mock_api):
    assert isinstance(connector, ConnectorMatrix)
    assert connector.access_token == "token"
    await connector.connect()

    assert mock_api.called("/_matrix/client/r0/account/whoami")

    assert "Invalid macaroon passed." in caplog.records[0].message
    assert "M_UNKNOWN_TOKEN" in caplog.records[0].message


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
@pytest.mark.add_response(
    "/_matrix/client/r0/join/#test:localhost", "POST", {"room_id": "!12355:localhost"}
)
@pytest.mark.asyncio
async def test_connect_login(
    opsdroid, connector, double_filter_response, single_message_sync_response, mock_api
):
    assert isinstance(connector, ConnectorMatrix)
    await connector.connect()

    assert mock_api.called("/_matrix/client/r0/login")
    assert (
        mock_api.call_count("/_matrix/client/r0/user/@opsdroid:localhost/filter") == 2
    )
    assert mock_api.called("/_matrix/client/r0/sync")
    assert mock_api.called("/_matrix/client/r0/join/#test:localhost")

    assert connector.access_token == connector.connection.access_token == "abc123"


@pytest.mark.matrix_connector_config("login_config")
@pytest.mark.add_response(
    "/_matrix/client/r0/login",
    "POST",
    {
        "errcode": "M_FORBIDDEN",
        "error": "Invalid password",
    },
    status=403,
)
@pytest.mark.asyncio
async def test_connect_login_error(caplog, opsdroid, connector, mock_api):
    assert isinstance(connector, ConnectorMatrix)
    await connector.connect()

    assert mock_api.called("/_matrix/client/r0/login")

    assert "Invalid password" in caplog.records[0].message
    assert "M_FORBIDDEN" in caplog.records[0].message

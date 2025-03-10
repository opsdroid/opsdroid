import logging

import pytest
from opsdroid.connector.matrix import ConnectorMatrix


def test_constructor(opsdroid, default_config):
    connector = ConnectorMatrix(default_config, opsdroid)
    assert isinstance(connector, ConnectorMatrix)


@pytest.mark.matrix_connector_config("token_config")
@pytest.mark.anyio
async def test_connect_access_token(
    opsdroid,
    connector,
    double_filter_response,
    single_message_sync_response,
    mock_whoami_join,
    mock_api,
):
    assert isinstance(connector, ConnectorMatrix)
    assert connector.access_token == "token"
    await connector.connect()
    await connector.disconnect()

    assert mock_api.called("/_matrix/client/v3/account/whoami")
    assert mock_api.called("/_matrix/client/v3/sync")
    assert mock_api.called("/_matrix/client/v3/join/#test:localhost")

    whoami_call = mock_api.get_request("/_matrix/client/v3/account/whoami", "GET", 0)
    assert "Authorization" in whoami_call.headers
    assert whoami_call.headers["Authorization"] == "Bearer token"


@pytest.mark.matrix_connector_config("token_config")
@pytest.mark.add_response(
    "/_matrix/client/v3/account/whoami",
    "GET",
    {"errcode": "M_UNKNOWN_TOKEN", "error": "Invalid macaroon passed."},
    status=401,
)
@pytest.mark.anyio
async def test_connect_invalid_access_token(caplog, opsdroid, connector, mock_api):
    assert isinstance(connector, ConnectorMatrix)
    assert connector.access_token == "token"
    await connector.connect()
    await connector.disconnect()

    assert mock_api.called("/_matrix/client/v3/account/whoami")

    assert "Error validating response: 'user_id'" in caplog.records[0].message
    assert "Invalid macaroon passed." in caplog.records[1].message
    assert "M_UNKNOWN_TOKEN" in caplog.records[1].message


@pytest.mark.matrix_connector_config("login_config")
@pytest.mark.add_response(
    "/_matrix/client/v3/login",
    "POST",
    {
        "user_id": "@opsdroid:localhost",
        "access_token": "abc123",
        "device_id": "GHTYAJCE",
    },
)
@pytest.mark.anyio
async def test_connect_login(
    opsdroid,
    connector,
    double_filter_response,
    single_message_sync_response,
    mock_whoami_join,
    mock_api,
):
    assert isinstance(connector, ConnectorMatrix)
    await connector.connect()
    await connector.disconnect()

    assert mock_api.called("/_matrix/client/v3/login")

    assert connector.access_token == connector.connection.access_token == "abc123"


@pytest.mark.matrix_connector_config("login_config")
@pytest.mark.add_response(
    "/_matrix/client/v3/login",
    "POST",
    {"errcode": "M_FORBIDDEN", "error": "Invalid password"},
    status=403,
)
@pytest.mark.anyio
async def test_connect_login_error(caplog, opsdroid, connector, mock_api):
    assert isinstance(connector, ConnectorMatrix)
    await connector.connect()
    await connector.disconnect()

    assert mock_api.called("/_matrix/client/v3/login")

    assert "Error validating response: 'user_id'" in caplog.records[0].message
    assert "Invalid password" in caplog.records[1].message
    assert "M_FORBIDDEN" in caplog.records[1].message


@pytest.mark.matrix_connector_config("token_config")
@pytest.mark.add_response(
    "/_matrix/client/v3/account/whoami", "GET", {"user_id": "@opsdroid:localhost"}
)
@pytest.mark.add_response(
    "/_matrix/client/v3/join/#test:localhost",
    "POST",
    {"errcode": "M_FORBIDDEN", "error": "You are not invited to this room."},
    status=403,
)
@pytest.mark.anyio
async def test_connect_join_fail(
    opsdroid,
    connector,
    double_filter_response,
    single_message_sync_response,
    mock_api,
    caplog,
):
    assert isinstance(connector, ConnectorMatrix)
    assert connector.access_token == "token"
    await connector.connect()
    await connector.disconnect()

    assert (
        "opsdroid.connector.matrix.connector",
        logging.ERROR,
        "Error while joining room: #test:localhost, Message: You are not invited to this room. (status code M_FORBIDDEN)",
    ) in caplog.record_tuples


@pytest.mark.matrix_connector_config(
    {"access_token": "token", "rooms": {"main": "#test:localhost"}, "nick": "opsdroid"}
)
@pytest.mark.add_response(
    "/_matrix/client/v3/profile/@opsdroid:localhost/displayname",
    "PUT",
    {"errcode": "M_FORBIDDEN", "error": "Invalid user"},
    status=403,
)
@pytest.mark.anyio
async def test_connect_set_nick_errors(
    opsdroid,
    connector,
    double_filter_response,
    single_message_sync_response,
    mock_whoami_join,
    mock_api,
    caplog,
):
    await connector.connect()
    await connector.disconnect()

    assert (
        "Error validating response: 'displayname' is a required property" in caplog.text
    )
    assert "Error fetching current display_name" in caplog.text
    assert "M_FORBIDDEN" in caplog.text

    caplog.clear()


@pytest.mark.matrix_connector_config(
    {"access_token": "token", "rooms": {"main": "#test:localhost"}, "nick": "opsdroid"}
)
@pytest.mark.add_response(
    "/_matrix/client/v3/profile/@opsdroid:localhost/displayname", "PUT", {}
)
@pytest.mark.add_response(
    "/_matrix/client/v3/profile/@opsdroid:localhost/displayname",
    "GET",
    {"displayname": "Wibble"},
)
@pytest.mark.anyio
async def test_connect_set_nick(
    opsdroid,
    connector,
    double_filter_response,
    single_message_sync_response,
    mock_whoami_join,
    mock_api,
):
    await connector.connect()
    await connector.disconnect()

    assert mock_api.called(
        "/_matrix/client/v3/profile/@opsdroid:localhost/displayname", "GET"
    )
    assert mock_api.called(
        "/_matrix/client/v3/profile/@opsdroid:localhost/displayname", "PUT"
    )

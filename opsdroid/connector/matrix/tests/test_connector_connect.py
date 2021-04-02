import pytest
import logging

from opsdroid.connector.matrix import ConnectorMatrix


def test_constructor(opsdroid, default_config):
    connector = ConnectorMatrix(default_config, opsdroid)
    assert isinstance(connector, ConnectorMatrix)


@pytest.mark.matrix_connector_config("token_config")
@pytest.mark.asyncio
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

    assert mock_api.called("/_matrix/client/r0/account/whoami")
    assert (
        mock_api.call_count("/_matrix/client/r0/user/@opsdroid:localhost/filter") == 2
    )
    assert mock_api.called("/_matrix/client/r0/sync")
    assert mock_api.called("/_matrix/client/r0/join/#test:localhost")

    whoami_call = mock_api.get_request("/_matrix/client/r0/account/whoami", "GET", 0)
    assert "access_token" in whoami_call.query
    assert whoami_call.query["access_token"] == "token"


@pytest.mark.matrix_connector_config("token_config")
@pytest.mark.add_response(
    "/_matrix/client/r0/account/whoami",
    "GET",
    {"errcode": "M_UNKNOWN_TOKEN", "error": "Invalid macaroon passed."},
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
@pytest.mark.asyncio
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
    {"errcode": "M_FORBIDDEN", "error": "Invalid password"},
    status=403,
)
@pytest.mark.asyncio
async def test_connect_login_error(caplog, opsdroid, connector, mock_api):
    assert isinstance(connector, ConnectorMatrix)
    await connector.connect()

    assert mock_api.called("/_matrix/client/r0/login")

    assert "Invalid password" in caplog.records[0].message
    assert "M_FORBIDDEN" in caplog.records[0].message


@pytest.mark.matrix_connector_config("token_config")
@pytest.mark.add_response(
    "/_matrix/client/r0/account/whoami", "GET", {"user_id": "@opsdroid:localhost"}
)
@pytest.mark.add_response(
    "/_matrix/client/r0/join/#test:localhost",
    "POST",
    {"errcode": "M_FORBIDDEN", "error": "You are not invited to this room."},
    status=403,
)
@pytest.mark.asyncio
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

    assert caplog.record_tuples == [
        (
            "opsdroid.connector.matrix.connector",
            logging.ERROR,
            "Error while joining room: #test:localhost, Message: You are not invited to this room. (status code M_FORBIDDEN)",
        )
    ]


@pytest.mark.matrix_connector_config(
    {"access_token": "token", "rooms": {"main": "#test:localhost"}, "nick": "opsdroid"}
)
@pytest.mark.add_response(
    "/_matrix/client/r0/profile/@opsdroid:localhost/displayname",
    "PUT",
    {"errcode": "M_FORBIDDEN", "error": "Invalid user"},
    status=403,
)
@pytest.mark.asyncio
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

    assert caplog.record_tuples == [
        (
            "opsdroid.connector.matrix.connector",
            logging.WARNING,
            "Error fetching current display_name: unknown error (status code None)",
        ),
        (
            "opsdroid.connector.matrix.connector",
            logging.WARNING,
            "Error setting display_name: Invalid user (status code M_FORBIDDEN)",
        ),
    ]

    caplog.clear()


@pytest.mark.matrix_connector_config(
    {"access_token": "token", "rooms": {"main": "#test:localhost"}, "nick": "opsdroid"}
)
@pytest.mark.add_response(
    "/_matrix/client/r0/profile/@opsdroid:localhost/displayname", "PUT", {}
)
@pytest.mark.add_response(
    "/_matrix/client/r0/profile/@opsdroid:localhost/displayname",
    "GET",
    {"displayname": "Wibble"},
)
@pytest.mark.asyncio
async def test_connect_set_nick(
    opsdroid,
    connector,
    double_filter_response,
    single_message_sync_response,
    mock_whoami_join,
    mock_api,
):
    await connector.connect()
    assert mock_api.called(
        "/_matrix/client/r0/profile/@opsdroid:localhost/displayname", "GET"
    )
    assert mock_api.called(
        "/_matrix/client/r0/profile/@opsdroid:localhost/displayname", "PUT"
    )

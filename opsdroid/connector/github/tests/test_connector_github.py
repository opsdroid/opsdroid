import pytest
import asynctest.mock as amock

import asyncio
import os

from opsdroid.connector.github import ConnectorGitHub
from opsdroid.events import Message


def test_init(opsdroid):
    """Test that the connector is initialised properly."""
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)
    assert connector.default_target is None
    assert connector.name == "github"


def test_missing_token(opsdroid, caplog):
    """Test that attempt to connect without info raises an error."""
    ConnectorGitHub({})
    assert "Missing auth token!" in caplog.text


@pytest.mark.asyncio
async def test_connect(opsdroid):
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)

    with amock.patch("aiohttp.ClientSession.get") as patched_request:
        mockresponse = amock.CoroutineMock()
        mockresponse.status = 200
        mockresponse.json = amock.CoroutineMock(return_value={"login": "opsdroid"})
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(mockresponse)
        await connector.connect()

        assert connector.github_username == "opsdroid"
        assert connector.opsdroid.web_server.web_app.router.add_post.called


@pytest.mark.asyncio
async def test_connect_failure(opsdroid, caplog):
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)

    with amock.patch("aiohttp.ClientSession.get") as patched_request:
        mockresponse = amock.CoroutineMock()
        mockresponse.status = 401
        mockresponse.text = amock.CoroutineMock(
            return_value='{"message": "Bad credentials", "documentation_url": "https://developer.github.com/v3"}'
        )
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(mockresponse)
        await connector.connect()

        assert "Error connecting to GitHub" in caplog.text


@pytest.mark.asyncio
async def test_disconnect(opsdroid):
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)

    assert await connector.disconnect() is None


@pytest.mark.asyncio
async def test_get_comment(opsdroid):
    """Test a comment create event creates a message and parses it."""
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)
    with open(
        os.path.join(
            os.path.dirname(__file__), "responses", "github_comment_payload.json"
        ),
        "r",
    ) as f:
        mock_request = amock.CoroutineMock()
        mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()
        await connector.github_message_handler(mock_request)

        message = connector.opsdroid.parse.call_args[0][0]

        assert message.connector.name == "github"
        assert message.text == "hello"
        assert message.target == "opsdroid/opsdroid#237"
        assert connector.opsdroid.parse.called


@pytest.mark.asyncio
async def test_get_pr(opsdroid):
    """Test a PR create event creates a message and parses it."""
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)
    with open(
        os.path.join(os.path.dirname(__file__), "responses", "github_pr_payload.json"),
        "r",
    ) as f:
        mock_request = amock.CoroutineMock()
        mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()
        await connector.github_message_handler(mock_request)

        message = connector.opsdroid.parse.call_args[0][0]

        assert message.connector.name == "github"
        assert message.text == "hello world"
        assert message.target == "opsdroid/opsdroid-audio#175"
        assert connector.opsdroid.parse.called


@pytest.mark.asyncio
async def test_get_issue(opsdroid):
    """Test an issue create event creates a message and parses it."""
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)

    with open(
        os.path.join(
            os.path.dirname(__file__), "responses", "github_issue_payload.json"
        ),
        "r",
    ) as f:
        mock_request = amock.CoroutineMock()
        mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()
        await connector.github_message_handler(mock_request)
        message = connector.opsdroid.parse.call_args[0][0]
        assert message.connector.name == "github"
        assert message.text == "test"
        assert message.target == "opsdroid/opsdroid#740"
        assert connector.opsdroid.parse.called


@pytest.mark.asyncio
async def test_get_label(opsdroid):
    """Test a label create event doesn't create a message and parse it."""
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)

    with open(
        os.path.join(
            os.path.dirname(__file__), "responses", "github_label_payload.json"
        ),
        "r",
    ) as f:
        mock_request = amock.CoroutineMock()
        mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()
        await connector.github_message_handler(mock_request)
        assert not connector.opsdroid.parse.called


@pytest.mark.asyncio
async def test_get_no_action(opsdroid):
    """Test a status event doesn't create a message and parse it."""
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)

    with open(
        os.path.join(
            os.path.dirname(__file__), "responses", "github_status_payload.json"
        ),
        "r",
    ) as f:
        mock_request = amock.CoroutineMock()
        mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
        connector.opsdroid = amock.CoroutineMock()
        connector.opsdroid.parse = amock.CoroutineMock()
        await connector.github_message_handler(mock_request)
        assert not connector.opsdroid.parse.called


@pytest.mark.asyncio
async def test_listen(opsdroid):
    """Test the listen method.

    The GitHub connector listens using an API endoint and so the listen
    method should just pass and do nothing. We just need to test that it
    does not block.

    """
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)
    assert await connector.listen() is None


@pytest.mark.asyncio
async def test_respond(opsdroid):
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)
    with amock.patch("aiohttp.ClientSession.post") as patched_request:
        mockresponse = amock.CoroutineMock()
        mockresponse.status = 201
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(mockresponse)
        resp = await connector.send(
            Message(
                text="test",
                user="jacobtomlinson",
                target="opsdroid/opsdroid#1",
                connector=connector,
            )
        )
        assert patched_request.called
        assert resp


@pytest.mark.asyncio
async def test_respond_bot_short(opsdroid):
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)

    with amock.patch("aiohttp.ClientSession.post") as patched_request:
        mockresponse = amock.CoroutineMock()
        mockresponse.status = 201
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(mockresponse)
        connector.github_username = "opsdroid-bot"
        resp = await connector.send(
            Message(
                text="test",
                user="opsdroid-bot",
                target="opsdroid/opsdroid#1",
                connector=connector,
            )
        )
        assert not patched_request.called
        assert resp


@pytest.mark.asyncio
async def test_respond_failure(opsdroid):
    opsdroid = amock.CoroutineMock()
    connector = ConnectorGitHub({"name": "github", "token": "test"}, opsdroid=opsdroid)

    with amock.patch("aiohttp.ClientSession.post") as patched_request:
        mockresponse = amock.CoroutineMock()
        mockresponse.status = 400
        mockresponse.json = amock.CoroutineMock(return_value={"error": "some error"})
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(mockresponse)
        resp = await connector.send(
            Message(
                text="test",
                user="opsdroid-bot",
                target="opsdroid/opsdroid#1",
                connector=connector,
            )
        )
        assert patched_request.called
        assert not resp

"""Tests for the GitHub class."""
import pytest
import asynctest
import asynctest.mock as amock

import os.path

from opsdroid.cli.start import configure_lang
from opsdroid.connector.github import ConnectorGitHub
from opsdroid.events import Message


configure_lang({})


@pytest.fixture
async def connector(opsdroid, mock_api):
    connector = ConnectorGitHub(
        {"name": "github", "token": "abc123"}, opsdroid=opsdroid
    )
    opsdroid.web_server = amock.CoroutineMock()
    opsdroid.web_server.web_app = amock.CoroutineMock()
    opsdroid.web_server.web_app.router = amock.CoroutineMock()
    opsdroid.web_server.web_app.router.add_get = amock.CoroutineMock()
    opsdroid.web_server.web_app.router.add_post = amock.CoroutineMock()

    connector.github_api_url = mock_api.base_url

    return connector


def get_response_path(response):
    return os.path.join(os.path.dirname(__file__), "responses", response)


def test_init():
    """Test that the connector is initialised properly."""
    connector = ConnectorGitHub({"name": "github", "token": "test"})
    assert connector.default_target is None
    assert connector.name == "github"


def test_missing_token(caplog):
    """Test that attempt to connect without info raises an error."""
    ConnectorGitHub({})
    assert "Missing auth token!" in caplog.text


@pytest.mark.asyncio
async def test_connect(connector, mock_api):
    mock_api.add_response(
        "/user", "GET", get_response_path("github_user.json"), status=200
    )

    async def test():
        await connector.connect()

        assert mock_api.called("/user")
        assert mock_api.call_count("/user") == 1

        request = mock_api.get_request("/user")
        assert "Authorization" in request.headers
        assert "abc123" in request.headers["Authorization"]

        # Populated by the call to /user
        assert connector.github_username == "opsdroid"

    await mock_api.run_test(test)


@pytest.mark.asyncio
async def test_connect_failure(connector, mock_api, caplog):
    mock_api.add_response(
        "/user",
        "GET",
        get_response_path("github_user_bad_credentials.json"),
        status=401,
    )

    async def test():
        await connector.connect()
        assert "Bad credentials" in caplog.text

    await mock_api.run_test(test)


@pytest.mark.asyncio
async def test_disconnect(connector):
    assert await connector.disconnect() is None


@pytest.mark.asyncio
async def test_listen(connector):
    """Test the listen method.

    The GitHub connector listens using an API endoint and so the listen
    method should just pass and do nothing. We just need to test that it
    does not block.

    """
    assert await connector.listen() is None


@pytest.mark.asyncio
async def test_send(opsdroid, connector, mock_api):
    org, repo, issue = "opsdroid", "opsdroid", "1"
    api_url = f"/repos/{org}/{repo}/issues/{issue}/comments"
    mock_api.add_response(api_url, "POST", None, status=201)

    async def test():
        await opsdroid.send(
            Message(
                text="test",
                user="jacobtomlinson",
                target=f"{org}/{repo}#{issue}",
                connector=connector,
            )
        )
        assert mock_api.called(api_url)

    await mock_api.run_test(test)


@pytest.mark.asyncio
async def test_send_failure(opsdroid, connector, mock_api, caplog):
    org, repo, issue = "opsdroid", "opsdroid", "1"
    api_url = f"/repos/{org}/{repo}/issues/{issue}/comments"
    mock_api.add_response(
        api_url, "POST", get_response_path("github_send_failure.json"), status=400
    )

    async def test():
        await opsdroid.send(
            Message(
                text="test",
                user="jacobtomlinson",
                target=f"{org}/{repo}#{issue}",
                connector=connector,
            )
        )
        assert mock_api.called(api_url)
        assert "some error" in caplog.text

    await mock_api.run_test(test)


@pytest.mark.asyncio
async def test_do_not_send_to_self(opsdroid, connector, mock_api):
    org, repo, issue = "opsdroid", "opsdroid", "1"
    api_url = f"/repos/{org}/{repo}/issues/{issue}/comments"
    mock_api.add_response(api_url, "POST", None, status=201)
    connector.github_username = "opsdroid-bot"

    async def test():
        await opsdroid.send(
            Message(
                text="test",
                user="opsdroid-bot",
                target=f"{org}/{repo}#{issue}",
                connector=connector,
            )
        )
        assert not mock_api.called(api_url)

    await mock_api.run_test(test)


class TestConnectorGitHubAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid github connector class."""

    def setUp(self):
        opsdroid = amock.CoroutineMock()
        self.connector = ConnectorGitHub(
            {"name": "github", "token": "test"}, opsdroid=opsdroid
        )

    async def test_get_comment(self):
        """Test a comment create event creates a message and parses it."""
        with open(
            os.path.join(
                os.path.dirname(__file__), "responses", "github_comment_payload.json"
            ),
            "r",
        ) as f:
            mock_request = amock.CoroutineMock()
            mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
            self.connector.opsdroid = amock.CoroutineMock()
            self.connector.opsdroid.parse = amock.CoroutineMock()
            await self.connector.github_message_handler(mock_request)
            message = self.connector.opsdroid.parse.call_args[0][0]
            self.assertEqual(message.connector.name, "github")
            self.assertEqual(message.text, "hello")
            self.assertEqual(message.target, "opsdroid/opsdroid#237")
            self.assertTrue(self.connector.opsdroid.parse.called)

    async def test_get_pr(self):
        """Test a PR create event creates a message and parses it."""
        with open(
            os.path.join(
                os.path.dirname(__file__), "responses", "github_pr_payload.json"
            ),
            "r",
        ) as f:
            mock_request = amock.CoroutineMock()
            mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
            self.connector.opsdroid = amock.CoroutineMock()
            self.connector.opsdroid.parse = amock.CoroutineMock()
            await self.connector.github_message_handler(mock_request)
            message = self.connector.opsdroid.parse.call_args[0][0]
            self.assertEqual(message.connector.name, "github")
            self.assertEqual(message.text, "hello world")
            self.assertEqual(message.target, "opsdroid/opsdroid-audio#175")
            self.assertTrue(self.connector.opsdroid.parse.called)

    async def test_get_issue(self):
        """Test an issue create event creates a message and parses it."""
        with open(
            os.path.join(
                os.path.dirname(__file__), "responses", "github_issue_payload.json"
            ),
            "r",
        ) as f:
            mock_request = amock.CoroutineMock()
            mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
            self.connector.opsdroid = amock.CoroutineMock()
            self.connector.opsdroid.parse = amock.CoroutineMock()
            await self.connector.github_message_handler(mock_request)
            message = self.connector.opsdroid.parse.call_args[0][0]
            self.assertEqual(message.connector.name, "github")
            self.assertEqual(message.text, "test")
            self.assertEqual(message.target, "opsdroid/opsdroid#740")
            self.assertTrue(self.connector.opsdroid.parse.called)

    async def test_get_label(self):
        """Test a label create event doesn't create a message and parse it."""
        with open(
            os.path.join(
                os.path.dirname(__file__), "responses", "github_label_payload.json"
            ),
            "r",
        ) as f:
            mock_request = amock.CoroutineMock()
            mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
            self.connector.opsdroid = amock.CoroutineMock()
            self.connector.opsdroid.parse = amock.CoroutineMock()
            await self.connector.github_message_handler(mock_request)
            self.assertFalse(self.connector.opsdroid.parse.called)

    async def test_get_no_action(self):
        """Test a status event doesn't create a message and parse it."""
        with open(
            os.path.join(
                os.path.dirname(__file__), "responses", "github_status_payload.json"
            ),
            "r",
        ) as f:
            mock_request = amock.CoroutineMock()
            mock_request.post = amock.CoroutineMock(return_value={"payload": f.read()})
            self.connector.opsdroid = amock.CoroutineMock()
            self.connector.opsdroid.parse = amock.CoroutineMock()
            await self.connector.github_message_handler(mock_request)
            self.assertFalse(self.connector.opsdroid.parse.called)

"""Tests for the GitHub class."""
import pytest
from asynctest.mock import CoroutineMock
from pathlib import Path


from opsdroid.connector.github import ConnectorGitHub
from opsdroid.events import Message
from opsdroid.matchers import match_event
from opsdroid.testing import call_endpoint, running_opsdroid


# these strings are used in several tests
ORG, REPO, ISSUE = "opsdroid", "opsdroid", "1"
ISSUE_TARGET = f"{ORG}/{REPO}#{ISSUE}"
COMMENTS_URI = f"/repos/{ORG}/{REPO}/issues/{ISSUE}/comments"


@pytest.fixture
async def connector(opsdroid, mock_api_obj):
    opsdroid.config["connectors"] = {
        "github": {"token": "abc123", "api_base_url": mock_api_obj.base_url}
    }
    await opsdroid.load()
    return opsdroid.get_connector("github")


def get_response_path(response):
    return Path(__file__).parent / "responses" / response


def get_webhook_payload(path):
    with open(get_response_path(path), "r") as fh:
        return {"payload": fh.read()}


def test_init():
    """Test that the connector is initialised properly."""
    connector = ConnectorGitHub({"name": "github", "token": "test"})
    assert connector.default_target is None
    assert connector.name == "github"


def test_missing_token(caplog):
    """Test that attempt to connect without info raises an error."""
    ConnectorGitHub({})
    assert "Missing auth token!" in caplog.text


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_connect(connector, mock_api):
    await connector.connect()

    assert mock_api.called("/user")
    assert mock_api.call_count("/user") == 1

    request = mock_api.get_request("/user")
    assert "Authorization" in request.headers
    assert "abc123" in request.headers["Authorization"]

    # Populated by the call to /user
    assert connector.github_username == "opsdroid"


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user_bad_credentials.json"), status=401
)
@pytest.mark.asyncio
async def test_connect_failure(connector, mock_api, caplog):
    await connector.connect()
    assert "Bad credentials" in caplog.text


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


@pytest.mark.add_response(COMMENTS_URI, "POST", None, status=201)
@pytest.mark.asyncio
async def test_send(opsdroid, connector, mock_api):
    await opsdroid.send(
        Message(
            text="test",
            user="jacobtomlinson",
            target=ISSUE_TARGET,
            connector=connector,
        )
    )
    assert mock_api.called(COMMENTS_URI)


@pytest.mark.add_response(
    COMMENTS_URI,
    "POST",
    get_response_path("github_send_failure.json"),
    status=400,
)
@pytest.mark.asyncio
async def test_send_failure(opsdroid, connector, mock_api, caplog):
    await opsdroid.send(
        Message(
            text="test",
            user="jacobtomlinson",
            target=ISSUE_TARGET,
            connector=connector,
        )
    )
    assert mock_api.called(COMMENTS_URI)
    assert "some error" in caplog.text


@pytest.mark.add_response(COMMENTS_URI, "POST", status=201)
@pytest.mark.asyncio
async def test_do_not_send_to_self(opsdroid, connector, mock_api):
    connector.github_username = "opsdroid-bot"

    await opsdroid.send(
        Message(
            text="test",
            user="opsdroid-bot",
            target=ISSUE_TARGET,
            connector=connector,
        )
    )
    assert not mock_api.called(COMMENTS_URI)


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_receive_comment(opsdroid, connector, mock_api):
    """Test a comment create event creates a message and parses it."""

    @match_event(Message)
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "github"
        assert event.text == "hello"
        assert event.target == "opsdroid/opsdroid#237"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_comment_payload.json"),
        )
        assert resp.status == 201


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_receive_pr(opsdroid, connector, mock_api):
    """Test a PR create event creates a message and parses it."""

    @match_event(Message)
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "github"
        assert event.text == "hello world"
        assert event.target == "opsdroid/opsdroid-audio#175"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_pr_payload.json"),
        )
        assert resp.status == 201


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_receive_issue(opsdroid, connector, mock_api):
    """Test a PR create event creates a message and parses it."""

    @match_event(Message)
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "github"
        assert event.text == "test"
        assert event.target == "opsdroid/opsdroid#740"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_issue_payload.json"),
        )
        assert resp.status == 201


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_receive_label(opsdroid, connector, mock_api):
    """Test a PR create event creates a message and parses it."""

    test_skill = match_event(Message)(CoroutineMock())
    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_label_payload.json"),
        )
        assert resp.status == 200

    assert not test_skill.called


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_receive_status(opsdroid, connector, mock_api):
    """Test a PR create event creates a message and parses it."""

    test_skill = match_event(Message)(CoroutineMock())
    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_status_payload.json"),
        )
        assert resp.status == 201

    assert not test_skill.called

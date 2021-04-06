"""Tests for the GitHub class."""
import logging
from pathlib import Path

import asynctest.mock as amock
import opsdroid.connector.github.events as github_event
import pytest
from asynctest.mock import CoroutineMock
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


def test_missing_secret(caplog):
    """Test that missing secret will log a message."""
    ConnectorGitHub({})
    assert "You should use it to improve security" in caplog.text


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_connect(connector, mock_api):
    await connector.connect()

    assert mock_api.called("/user")
    assert mock_api.call_count("/user") == 1

    request = mock_api.get_request("/user", "GET")
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
            text="test", user="jacobtomlinson", target=ISSUE_TARGET, connector=connector
        )
    )
    assert mock_api.called(COMMENTS_URI)


@pytest.mark.add_response(
    COMMENTS_URI, "POST", get_response_path("github_send_failure.json"), status=400
)
@pytest.mark.asyncio
async def test_send_failure(opsdroid, connector, mock_api, caplog):
    await opsdroid.send(
        Message(
            text="test", user="jacobtomlinson", target=ISSUE_TARGET, connector=connector
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
            text="test", user="opsdroid-bot", target=ISSUE_TARGET, connector=connector
        )
    )
    assert not mock_api.called(COMMENTS_URI)


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_receive_comment(opsdroid, connector, mock_api):
    """Test a comment create event creates a message and parses it."""

    @match_event(github_event.IssueCommented)
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "github"
        assert event.target == "opsdroid/opsdroid#237"
        assert event.comment == "hello"
        assert event.issue_title == "test issue, please ignore"
        assert (
            event.comment_url
            == "https://api.github.com/repos/opsdroid/opsdroid/issues/comments/439318644"
        )
        assert event.user == "jacobtomlinson"

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

    @match_event(github_event.PROpened)
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "github"
        assert event.target == "opsdroid/opsdroid-audio#175"
        assert event.title == "Update pytest-timeout to 1.3.3"
        assert event.description == "hello world"

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
async def test_close_pr(opsdroid, connector, mock_api):
    """Test a PR close event creates an event and parses it."""

    @match_event(github_event.PRClosed)
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "github"
        assert event.target == "opsdroid/opsdroid-audio#175"
        assert event.title == "Update pytest-timeout to 1.3.3"
        assert event.closed_by == "pyup-bot"
        assert event.user == "pyup-bot"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_pr_closed_payload.json"),
        )
        assert resp.status == 201


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_pr_merged(opsdroid, connector, mock_api):
    """Test a PR merge event creates an event and parses it."""

    @match_event(github_event.PRMerged)
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "github"
        assert event.target == "opsdroid/opsdroid-audio#175"
        assert event.title == "Update pytest-timeout to 1.3.3"
        assert event.description == "hello world"
        assert event.merger == "FabioRosado"
        assert event.user == "pyup-bot"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_pr_merged_payload.json"),
        )
        assert resp.status == 201


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_check_started(opsdroid, connector, mock_api):
    """Test a check started event creates an event and parses it."""

    @match_event(github_event.CheckStarted)
    async def test_skill(opsdroid, config, event):
        assert event.action == "created"
        assert event.status == "queued"
        assert not event.conclusion
        assert event.repository == "Hello-World"
        assert event.sender == "Codertocat"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_check_created_payload.json"),
        )
        assert resp.status == 201


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_check_failed(opsdroid, connector, mock_api):
    """Test a check failed event creates an event and parses it."""

    @match_event(github_event.CheckFailed)
    async def test_skill(opsdroid, config, event):
        assert event.action == "completed"
        assert event.status == "completed"
        assert event.conclusion == "failure"
        assert event.repository == "Hello-World"
        assert event.sender == "Codertocat"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_check_failed_payload.json"),
        )
        assert resp.status == 201


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_check_passed(opsdroid, connector, mock_api):
    """Test a check passed event creates an event and parses it."""

    @match_event(github_event.CheckPassed)
    async def test_skill(opsdroid, config, event):
        assert event.action == "completed"
        assert event.status == "completed"
        assert event.conclusion == "success"
        assert event.repository == "Hello-World"
        assert event.sender == "Codertocat"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_check_passed_payload.json"),
        )
        assert resp.status == 201


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_check_completed(opsdroid, connector, mock_api):
    """Test a check completed event creates an event and parses it."""

    @match_event(github_event.CheckCompleted)
    async def test_skill(opsdroid, config, event):
        assert event.action == "completed"
        assert event.status == "completed"
        assert event.conclusion == "timed_out"
        assert event.repository == "Hello-World"
        assert event.sender == "Codertocat"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_check_completed_payload.json"),
        )
        assert resp.status == 201


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_receive_issue(opsdroid, connector, mock_api):
    """Test a issue create event creates a message and parses it."""

    @match_event(github_event.IssueCreated)
    async def test_skill(opsdroid, config, event):
        assert event.user == "jacobtomlinson"
        assert event.title == "A test please ignore"
        assert event.description == "test"

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
async def test_received_issue_close(opsdroid, connector, mock_api):
    """Test a issue close event creates an event and parses it."""

    @match_event(github_event.IssueClosed)
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "github"
        assert event.target == "FabioRosado/github-actions-test#10"
        assert event.title == "Test integration"
        assert event.description == "this is a test for the integration"
        assert event.user == "FabioRosado"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_issue_close_payload.json"),
        )
        assert resp.status == 201


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_receive_label(opsdroid, connector, mock_api):
    """Test a receive label event creates a message and parses it."""

    @match_event(github_event.Unlabeled)
    async def test_skill(opsdroid, config, event):
        assert event.labels == "bug"
        assert event.state == "open"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_label_payload.json"),
        )
        assert resp.status == 201


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_receive_unlabel_event(opsdroid, connector, mock_api):
    """Test a unlabel event creates a message and parses it."""

    @match_event(github_event.Unlabeled)
    async def test_skill(opsdroid, config, event):
        assert event.labels == "bug"
        assert event.state == "open"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_unlabel_payload.json"),
        )
        assert resp.status == 201


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


@pytest.mark.asyncio
async def test_validate_request(opsdroid):
    connector_config = {"secret": "client-secret", "token": "test"}
    connector = ConnectorGitHub(connector_config, opsdroid=opsdroid)
    request = amock.CoroutineMock()
    request.headers = {
        "X-Hub-Signature-256": "sha256=fcfa24b327e3467f1586cc1ace043c016cabfe9c15dabc0020aca45440338be9"
    }

    request.read = amock.CoroutineMock()
    request.read.return_value = b'{"test": "test"}'

    validation = await connector.validate_request(request, "test")

    assert validation


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_no_key_in_payload(opsdroid, connector, mock_api, caplog):
    """Test if payload doesn't contain 'action' key."""

    @match_event(github_event.PROpened)
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "github"
        assert event.target == "opsdroid/opsdroid-audio#175"
        assert event.title == "Update pytest-timeout to 1.3.3"
        assert event.description == "hello world"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        caplog.set_level(logging.DEBUG)
        await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_user_forked_payload.json"),
        )
        assert "Key 'action' not found in payload" in caplog.text


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_no_event_to_parse(opsdroid, connector, mock_api, caplog):
    """Test a payload that github doesn't know how to parse."""

    @match_event(github_event.PROpened)
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "github"
        assert event.target == "opsdroid/opsdroid-audio#175"
        assert event.title == "Update pytest-timeout to 1.3.3"
        assert event.description == "hello world"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        caplog.set_level(logging.DEBUG)
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_deployment_payload.json"),
        )
        assert "No message to respond to." in caplog.text
        assert resp.status == 200


@pytest.fixture
async def connector_with_validation(opsdroid, mock_api_obj):
    opsdroid.config["connectors"] = {
        "github": {
            "token": "abc123",
            "api_base_url": mock_api_obj.base_url,
            "secret": "test",
        }
    }
    await opsdroid.load()
    return opsdroid.get_connector("github")


@pytest.mark.add_response(
    "/user", "GET", get_response_path("github_user.json"), status=200
)
@pytest.mark.asyncio
async def test_invalid_request(opsdroid, connector_with_validation, mock_api, caplog):
    """Test a payload with an invalid request."""

    @match_event(github_event.PROpened)
    async def test_skill(opsdroid, config, event):
        assert event.connector.name == "github"
        assert event.target == "opsdroid/opsdroid-audio#175"
        assert event.title == "Update pytest-timeout to 1.3.3"
        assert event.description == "hello world"

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        caplog.set_level(logging.DEBUG)
        resp = await call_endpoint(
            opsdroid,
            "/connector/github",
            "POST",
            data=get_webhook_payload("github_deployment_payload.json"),
        )
        assert resp.status == 401

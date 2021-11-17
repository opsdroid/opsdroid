# import os
# import asyncio
# from unittest import mock
# import json
import logging
from pathlib import Path

import asynctest.mock as amock

# import opsdroid.events as opsdroid_events
import opsdroid.connector.gitlab.events as gitlab_events
import pytest
from opsdroid.connector.gitlab import ConnectorGitlab
from opsdroid.matchers import match_event
from opsdroid.testing import call_endpoint, running_opsdroid


@pytest.fixture
async def connector(opsdroid, mock_api_obj):
    opsdroid.config["connectors"] = {"gitlab": {"webhook-token": "secret-stuff!"}}
    opsdroid.config["web"] = {"base-url": mock_api_obj.base_url}

    await opsdroid.load()
    return opsdroid.get_connector("gitlab")


def get_response_path(response: str) -> Path:
    return Path(__file__).parent / "gitlab_response_payloads" / response


def get_webhook_payload(path: str) -> str:
    with open(get_response_path(path), "r") as fh:
        return fh.read()


def test_app_init():
    """Test that the connector is initialised properly when using Gitlab"""
    connector = ConnectorGitlab({"name": "gitlab", "webhook-token": "secret-stuff!"})
    assert connector.name == "gitlab"
    assert connector.webhook_token == "secret-stuff!"


def test_init(opsdroid):
    connector = ConnectorGitlab({}, opsdroid=opsdroid)
    assert connector.name == "gitlab"
    assert connector.opsdroid == opsdroid
    assert connector.base_url is None


def test_optional_config(opsdroid):
    config = {
        "name": "my-gitlab",
        "forward-url": "http://my-awesome-url",
        "webhook-token": "secret-stuff",
    }

    connector = ConnectorGitlab(config, opsdroid)
    assert connector.name == "my-gitlab"
    assert connector.base_url == "http://my-awesome-url"
    assert connector.webhook_token == "secret-stuff"


def test_base_url(opsdroid):
    opsdroid.config["web"] = {"base-url": "http://example.com"}

    connector = ConnectorGitlab({}, opsdroid)

    assert connector.base_url == "http://example.com"


@pytest.mark.asyncio
async def test_validate_request(opsdroid):
    config = {"webhook-token": "secret-stuff"}
    connector = ConnectorGitlab(config, opsdroid)

    request = amock.CoroutineMock()
    request.headers = {"X-Gitlab-Token": "secret-stuff"}

    is_valid = await connector.validate_request(request)

    assert is_valid

    fake_request = amock.CoroutineMock()
    request.headers = {}

    is_valid = await connector.validate_request(fake_request)

    assert not is_valid


@pytest.mark.asyncio
async def test_listen(connector):
    assert await connector.listen() is None


@pytest.mark.asyncio
async def test_issue_created(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.IssueCreated)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/issues/1"
        assert event.connector.name == "gitlab"
        assert event.target == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "New test issue"
        assert event.description == "Test description"
        assert event.labels == ["test-label"]
        assert event.url == url
        logging.getLogger(__name__).info("Test skill complete")

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/gitlab",
            "POST",
            headers={
                "X-Gitlab-Token": "secret-stuff!",
                "Content-Type": "application/json",
            },
            data=get_webhook_payload("issue_created.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_no_token_returns_401(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.IssueCreated)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/issues/1"
        assert event.connector.name == "gitlab"
        assert event.target == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "New test issue"
        assert event.description == "Test description"
        assert event.labels == ["test-label"]
        assert event.url == url
        logging.getLogger(__name__).info("Test skill complete")

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/gitlab",
            "POST",
            headers={
                "Content-Type": "application/json",
            },
            data=get_webhook_payload("issue_created.json"),
        )

        assert resp.status == 401
        assert "Test skill complete" not in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_issue_closed(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.IssueClosed)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/issues/1"
        assert event.connector.name == "gitlab"
        assert event.target == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "New test issue"
        assert event.description == "This should have been filled"
        assert event.labels == ["test-label"]
        assert event.url == url
        logging.getLogger(__name__).info("Test skill complete")

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/gitlab",
            "POST",
            headers={
                "X-Gitlab-Token": "secret-stuff!",
                "Content-Type": "application/json",
            },
            data=get_webhook_payload("issue_closed.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_generic_issue_event(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.GenericGitlabEvent)
    async def test_skill(opsdroid, config, event):
        url = "http://example.com/mike/diaspora"
        breakpoint()
        assert event.connector.name == "gitlab"
        assert event.target == url
        assert event.project == "Diaspora"
        assert event.user == "jsmith"
        assert event.title is None
        assert event.description is None
        assert event.labels == []
        assert event.url == url
        logging.getLogger(__name__).info("Test skill complete")

    opsdroid.register_skill(test_skill, config={"name": "test"})

    async with running_opsdroid(opsdroid):
        resp = await call_endpoint(
            opsdroid,
            "/connector/gitlab",
            "POST",
            headers={
                "X-Gitlab-Token": "secret-stuff!",
                "Content-Type": "application/json",
            },
            data=get_webhook_payload("push.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text

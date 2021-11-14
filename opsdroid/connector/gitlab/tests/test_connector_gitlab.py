# import os
# import logging
# import asyncio
# from unittest import mock
import asynctest.mock as amock

# import opsdroid.events as opsdroid_events
# import opsdroid.connector.gitlab.events as gitlab_events
import pytest
from opsdroid.connector.gitlab import ConnectorGitlab


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

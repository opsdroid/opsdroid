# import os
# import logging
# import asyncio
# from unittest import mock
import pytest
import asynctest.mock as amock

from opsdroid.connector.gitlab import ConnectorGitlab

# import opsdroid.events as opsdroid_events
import opsdroid.connector.gitlab.events as gitlab_events


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
async def test_push_event(opsdroid, caplog):
    connector = ConnectorGitlab({}, opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "object_kind": "push",
        "event_name": "push",
        "before": "ec5305fc204a1788f299326d3660f277d6c754aa",
        "after": "ec5305fc204a1788f299326d3660f277d6c754aa",
        "ref": "refs/heads/main",
        "checkout_sha": "ec5305fc204a1788f299326d3660f277d6c754aa",
        "message": None,
        "user_id": 3612771,
        "user_name": "Fabio Rosado",
        "user_username": "FabioRosado",
        "user_email": "",
        "user_avatar": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
        "project_id": 30456730,
        "project": {
            "id": 30456730,
            "name": "test-project",
            "description": "",
            "web_url": "https://gitlab.com/FabioRosado/test-project",
            "avatar_url": None,
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "namespace": "Fabio Rosado",
            "visibility_level": 0,
            "path_with_namespace": "FabioRosado/test-project",
            "default_branch": "main",
            "ci_config_path": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "http_url": "https://gitlab.com/FabioRosado/test-project.git",
        },
        "commits": [
            {
                "id": "ec5305fc204a1788f299326d3660f277d6c754aa",
                "message": "Initial commit",
                "title": "Initial commit",
                "timestamp": "2021-10-14T18:07:33+00:00",
                "url": "https://gitlab.com/FabioRosado/test-project/-/commit/ec5305fc204a1788f299326d3660f277d6c754aa",
                "author": {"name": "Fabio Rosado", "email": "fabioglrosado@gmail.com"},
                "added": ["README.md"],
                "modified": [],
                "removed": [],
            }
        ],
        "total_commits_count": 1,
        "push_options": {},
        "repository": {
            "name": "test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "description": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "visibility_level": 0,
        },
    }
    assert connector


@pytest.mark.asyncio
async def test_tag_push_event(opsdroid, caplog):
    connector = ConnectorGitlab({}, opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "object_kind": "push",
        "event_name": "push",
        "before": "ec5305fc204a1788f299326d3660f277d6c754aa",
        "after": "ec5305fc204a1788f299326d3660f277d6c754aa",
        "ref": "refs/heads/main",
        "checkout_sha": "ec5305fc204a1788f299326d3660f277d6c754aa",
        "message": None,
        "user_id": 3612771,
        "user_name": "Fabio Rosado",
        "user_username": "FabioRosado",
        "user_email": "",
        "user_avatar": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
        "project_id": 30456730,
        "project": {
            "id": 30456730,
            "name": "test-project",
            "description": "",
            "web_url": "https://gitlab.com/FabioRosado/test-project",
            "avatar_url": None,
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "namespace": "Fabio Rosado",
            "visibility_level": 0,
            "path_with_namespace": "FabioRosado/test-project",
            "default_branch": "main",
            "ci_config_path": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "http_url": "https://gitlab.com/FabioRosado/test-project.git",
        },
        "commits": [
            {
                "id": "ec5305fc204a1788f299326d3660f277d6c754aa",
                "message": "Initial commit",
                "title": "Initial commit",
                "timestamp": "2021-10-14T18:07:33+00:00",
                "url": "https://gitlab.com/FabioRosado/test-project/-/commit/ec5305fc204a1788f299326d3660f277d6c754aa",
                "author": {"name": "Fabio Rosado", "email": "fabioglrosado@gmail.com"},
                "added": ["README.md"],
                "modified": [],
                "removed": [],
            }
        ],
        "total_commits_count": 1,
        "push_options": {},
        "repository": {
            "name": "test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "description": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "visibility_level": 0,
        },
    }
    assert connector


@pytest.mark.asyncio
async def test_issues_event(opsdroid, caplog):
    connector = ConnectorGitlab({}, opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "object_kind": "issue",
        "event_type": "issue",
        "user": {
            "id": 3612771,
            "name": "Fabio Rosado",
            "username": "FabioRosado",
            "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
            "email": "[REDACTED]",
        },
        "project": {
            "id": 30456730,
            "name": "test-project",
            "description": "",
            "web_url": "https://gitlab.com/FabioRosado/test-project",
            "avatar_url": None,
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "namespace": "Fabio Rosado",
            "visibility_level": 0,
            "path_with_namespace": "FabioRosado/test-project",
            "default_branch": "main",
            "ci_config_path": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "http_url": "https://gitlab.com/FabioRosado/test-project.git",
        },
        "object_attributes": {
            "author_id": 3612771,
            "closed_at": None,
            "confidential": False,
            "created_at": "2021-11-07T18:10:32.914Z",
            "description": "",
            "discussion_locked": None,
            "due_date": None,
            "id": 96886238,
            "iid": 1,
            "last_edited_at": None,
            "last_edited_by_id": None,
            "milestone_id": None,
            "moved_to_id": None,
            "duplicated_to_id": None,
            "project_id": 30456730,
            "relative_position": 513,
            "state_id": 1,
            "time_estimate": 0,
            "title": "New test issue",
            "updated_at": "2021-11-07T18:10:47.885Z",
            "updated_by_id": 3612771,
            "weight": None,
            "url": "https://gitlab.com/FabioRosado/test-project/-/issues/1",
            "total_time_spent": 0,
            "time_change": 0,
            "human_total_time_spent": None,
            "human_time_change": None,
            "human_time_estimate": None,
            "assignee_ids": [],
            "assignee_id": None,
            "labels": [
                {
                    "id": 22478741,
                    "title": "test-label",
                    "color": "#009966",
                    "project_id": 30456730,
                    "created_at": "2021-11-07T18:10:43.765Z",
                    "updated_at": "2021-11-07T18:10:43.765Z",
                    "template": False,
                    "description": None,
                    "type": "ProjectLabel",
                    "group_id": None,
                }
            ],
            "state": "opened",
            "severity": "unknown",
        },
        "labels": [
            {
                "id": 22478741,
                "title": "test-label",
                "color": "#009966",
                "project_id": 30456730,
                "created_at": "2021-11-07T18:10:43.765Z",
                "updated_at": "2021-11-07T18:10:43.765Z",
                "template": False,
                "description": None,
                "type": "ProjectLabel",
                "group_id": None,
            }
        ],
        "changes": {},
        "repository": {
            "name": "test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "description": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
        },
    }
    assert connector


@pytest.mark.asyncio
async def test_issue_closed_event(opsdroid, caplog):
    connector = ConnectorGitlab({}, opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "object_kind": "issue",
        "event_type": "issue",
        "user": {
            "id": 3612771,
            "name": "Fabio Rosado",
            "username": "FabioRosado",
            "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
            "email": "[REDACTED]",
        },
        "project": {
            "id": 30456730,
            "name": "test-project",
            "description": "",
            "web_url": "https://gitlab.com/FabioRosado/test-project",
            "avatar_url": None,
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "namespace": "Fabio Rosado",
            "visibility_level": 0,
            "path_with_namespace": "FabioRosado/test-project",
            "default_branch": "main",
            "ci_config_path": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "http_url": "https://gitlab.com/FabioRosado/test-project.git",
        },
        "object_attributes": {
            "author_id": 3612771,
            "closed_at": "2021-11-07 20:20:06 UTC",
            "confidential": False,
            "created_at": "2021-11-07 18:10:32 UTC",
            "description": "This should have been filled",
            "discussion_locked": None,
            "due_date": None,
            "id": 96886238,
            "iid": 1,
            "last_edited_at": "2021-11-07 20:17:43 UTC",
            "last_edited_by_id": 3612771,
            "milestone_id": None,
            "moved_to_id": None,
            "duplicated_to_id": None,
            "project_id": 30456730,
            "relative_position": 513,
            "state_id": 2,
            "time_estimate": 0,
            "title": "New test issue",
            "updated_at": "2021-11-07 20:20:06 UTC",
            "updated_by_id": 3612771,
            "weight": None,
            "url": "https://gitlab.com/FabioRosado/test-project/-/issues/1",
            "total_time_spent": 0,
            "time_change": 0,
            "human_total_time_spent": None,
            "human_time_change": None,
            "human_time_estimate": None,
            "assignee_ids": [],
            "assignee_id": None,
            "labels": [
                {
                    "id": 22478741,
                    "title": "test-label",
                    "color": "#009966",
                    "project_id": 30456730,
                    "created_at": "2021-11-07 18:10:43 UTC",
                    "updated_at": "2021-11-07 18:10:43 UTC",
                    "template": False,
                    "description": None,
                    "type": "ProjectLabel",
                    "group_id": None,
                }
            ],
            "state": "closed",
            "severity": "unknown",
            "action": "close",
        },
        "labels": [
            {
                "id": 22478741,
                "title": "test-label",
                "color": "#009966",
                "project_id": 30456730,
                "created_at": "2021-11-07 18:10:43 UTC",
                "updated_at": "2021-11-07 18:10:43 UTC",
                "template": False,
                "description": None,
                "type": "ProjectLabel",
                "group_id": None,
            }
        ],
        "changes": {
            "closed_at": {"previous": None, "current": "2021-11-07 20:20:06 UTC"},
            "state_id": {"previous": 1, "current": 2},
            "updated_at": {
                "previous": "2021-11-07 20:17:43 UTC",
                "current": "2021-11-07 20:20:06 UTC",
            },
        },
        "repository": {
            "name": "test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "description": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
        },
    }

    assert connector


@pytest.mark.asyncio
async def test_issue_message_edited_event(opsdroid, caplog):
    connector = ConnectorGitlab({}, opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "object_kind": "issue",
        "event_type": "issue",
        "user": {
            "id": 3612771,
            "name": "Fabio Rosado",
            "username": "FabioRosado",
            "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
            "email": "[REDACTED]",
        },
        "project": {
            "id": 30456730,
            "name": "test-project",
            "description": "",
            "web_url": "https://gitlab.com/FabioRosado/test-project",
            "avatar_url": None,
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "namespace": "Fabio Rosado",
            "visibility_level": 0,
            "path_with_namespace": "FabioRosado/test-project",
            "default_branch": "main",
            "ci_config_path": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "http_url": "https://gitlab.com/FabioRosado/test-project.git",
        },
        "object_attributes": {
            "author_id": 3612771,
            "closed_at": None,
            "confidential": False,
            "created_at": "2021-11-07 18:10:32 UTC",
            "description": "This should have been filled",
            "discussion_locked": None,
            "due_date": None,
            "id": 96886238,
            "iid": 1,
            "last_edited_at": "2021-11-07 20:17:43 UTC",
            "last_edited_by_id": 3612771,
            "milestone_id": None,
            "moved_to_id": None,
            "duplicated_to_id": None,
            "project_id": 30456730,
            "relative_position": 513,
            "state_id": 1,
            "time_estimate": 0,
            "title": "New test issue",
            "updated_at": "2021-11-07 20:17:43 UTC",
            "updated_by_id": 3612771,
            "weight": None,
            "url": "https://gitlab.com/FabioRosado/test-project/-/issues/1",
            "total_time_spent": 0,
            "time_change": 0,
            "human_total_time_spent": None,
            "human_time_change": None,
            "human_time_estimate": None,
            "assignee_ids": [],
            "assignee_id": None,
            "labels": [
                {
                    "id": 22478741,
                    "title": "test-label",
                    "color": "#009966",
                    "project_id": 30456730,
                    "created_at": "2021-11-07 18:10:43 UTC",
                    "updated_at": "2021-11-07 18:10:43 UTC",
                    "template": False,
                    "description": None,
                    "type": "ProjectLabel",
                    "group_id": None,
                }
            ],
            "state": "opened",
            "severity": "unknown",
            "action": "update",
        },
        "labels": [
            {
                "id": 22478741,
                "title": "test-label",
                "color": "#009966",
                "project_id": 30456730,
                "created_at": "2021-11-07 18:10:43 UTC",
                "updated_at": "2021-11-07 18:10:43 UTC",
                "template": False,
                "description": None,
                "type": "ProjectLabel",
                "group_id": None,
            }
        ],
        "changes": {
            "description": {"previous": "", "current": "This should have been filled"},
            "last_edited_at": {"previous": None, "current": "2021-11-07 20:17:43 UTC"},
            "last_edited_by_id": {"previous": None, "current": 3612771},
            "updated_at": {
                "previous": "2021-11-07 18:10:47 UTC",
                "current": "2021-11-07 20:17:43 UTC",
            },
        },
        "repository": {
            "name": "test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "description": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
        },
    }

    assert connector


@pytest.mark.asyncio
async def test_confidential_issue_event(opsdroid, caplog):
    connector = ConnectorGitlab({}, opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "object_kind": "issue",
        "event_type": "issue",
        "user": {
            "id": 3612771,
            "name": "Fabio Rosado",
            "username": "FabioRosado",
            "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
            "email": "[REDACTED]",
        },
        "project": {
            "id": 30456730,
            "name": "test-project",
            "description": "",
            "web_url": "https://gitlab.com/FabioRosado/test-project",
            "avatar_url": None,
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "namespace": "Fabio Rosado",
            "visibility_level": 0,
            "path_with_namespace": "FabioRosado/test-project",
            "default_branch": "main",
            "ci_config_path": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "http_url": "https://gitlab.com/FabioRosado/test-project.git",
        },
        "object_attributes": {
            "author_id": 3612771,
            "closed_at": None,
            "confidential": False,
            "created_at": "2021-11-07T18:10:32.914Z",
            "description": "",
            "discussion_locked": None,
            "due_date": None,
            "id": 96886238,
            "iid": 1,
            "last_edited_at": None,
            "last_edited_by_id": None,
            "milestone_id": None,
            "moved_to_id": None,
            "duplicated_to_id": None,
            "project_id": 30456730,
            "relative_position": 513,
            "state_id": 1,
            "time_estimate": 0,
            "title": "New test issue",
            "updated_at": "2021-11-07T18:10:47.885Z",
            "updated_by_id": 3612771,
            "weight": None,
            "url": "https://gitlab.com/FabioRosado/test-project/-/issues/1",
            "total_time_spent": 0,
            "time_change": 0,
            "human_total_time_spent": None,
            "human_time_change": None,
            "human_time_estimate": None,
            "assignee_ids": [],
            "assignee_id": None,
            "labels": [
                {
                    "id": 22478741,
                    "title": "test-label",
                    "color": "#009966",
                    "project_id": 30456730,
                    "created_at": "2021-11-07T18:10:43.765Z",
                    "updated_at": "2021-11-07T18:10:43.765Z",
                    "template": False,
                    "description": None,
                    "type": "ProjectLabel",
                    "group_id": None,
                }
            ],
            "state": "opened",
            "severity": "unknown",
        },
        "labels": [
            {
                "id": 22478741,
                "title": "test-label",
                "color": "#009966",
                "project_id": 30456730,
                "created_at": "2021-11-07T18:10:43.765Z",
                "updated_at": "2021-11-07T18:10:43.765Z",
                "template": False,
                "description": None,
                "type": "ProjectLabel",
                "group_id": None,
            }
        ],
        "changes": {},
        "repository": {
            "name": "test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "description": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
        },
    }

    assert connector


@pytest.mark.asyncio
async def test_merge_event(opsdroid, caplog):
    connector = ConnectorGitlab({}, opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "object_kind": "merge_request",
        "event_type": "merge_request",
        "user": {
            "id": 3612771,
            "name": "Fabio Rosado",
            "username": "FabioRosado",
            "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
            "email": "[REDACTED]",
        },
        "project": {
            "id": 30456730,
            "name": "test-project",
            "description": "",
            "web_url": "https://gitlab.com/FabioRosado/test-project",
            "avatar_url": None,
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "namespace": "Fabio Rosado",
            "visibility_level": 0,
            "path_with_namespace": "FabioRosado/test-project",
            "default_branch": "main",
            "ci_config_path": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "http_url": "https://gitlab.com/FabioRosado/test-project.git",
        },
        "object_attributes": {
            "assignee_id": 3612771,
            "author_id": 3612771,
            "created_at": "2021-11-07T18:14:50.582Z",
            "description": "",
            "head_pipeline_id": None,
            "id": 124957728,
            "iid": 1,
            "last_edited_at": None,
            "last_edited_by_id": None,
            "merge_commit_sha": None,
            "merge_error": None,
            "merge_params": {"force_remove_source_branch": "1"},
            "merge_status": "can_be_merged",
            "merge_user_id": None,
            "merge_when_pipeline_succeeds": False,
            "milestone_id": None,
            "source_branch": "test",
            "source_project_id": 30456730,
            "state_id": 1,
            "target_branch": "main",
            "target_project_id": 30456730,
            "time_estimate": 0,
            "title": "Test MR",
            "updated_at": "2021-11-07T18:14:50.582Z",
            "updated_by_id": None,
            "url": "https://gitlab.com/FabioRosado/test-project/-/merge_requests/1",
            "source": {
                "id": 30456730,
                "name": "test-project",
                "description": "",
                "web_url": "https://gitlab.com/FabioRosado/test-project",
                "avatar_url": None,
                "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
                "namespace": "Fabio Rosado",
                "visibility_level": 0,
                "path_with_namespace": "FabioRosado/test-project",
                "default_branch": "main",
                "ci_config_path": "",
                "homepage": "https://gitlab.com/FabioRosado/test-project",
                "url": "git@gitlab.com:FabioRosado/test-project.git",
                "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "http_url": "https://gitlab.com/FabioRosado/test-project.git",
            },
            "target": {
                "id": 30456730,
                "name": "test-project",
                "description": "",
                "web_url": "https://gitlab.com/FabioRosado/test-project",
                "avatar_url": None,
                "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
                "namespace": "Fabio Rosado",
                "visibility_level": 0,
                "path_with_namespace": "FabioRosado/test-project",
                "default_branch": "main",
                "ci_config_path": "",
                "homepage": "https://gitlab.com/FabioRosado/test-project",
                "url": "git@gitlab.com:FabioRosado/test-project.git",
                "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "http_url": "https://gitlab.com/FabioRosado/test-project.git",
            },
            "last_commit": {
                "id": "32117d8dffa9c0788c7a1842df1333772dc6aaf6",
                "message": "Add test\n",
                "title": "Add test",
                "timestamp": "2021-11-07T18:14:28+00:00",
                "url": "https://gitlab.com/FabioRosado/test-project/-/commit/32117d8dffa9c0788c7a1842df1333772dc6aaf6",
                "author": {"name": "FabioRosado", "email": "fabioglrosado@gmail.com"},
            },
            "work_in_progress": False,
            "total_time_spent": 0,
            "time_change": 0,
            "human_total_time_spent": None,
            "human_time_change": None,
            "human_time_estimate": None,
            "assignee_ids": [3612771],
            "state": "opened",
        },
        "labels": [],
        "changes": {},
        "repository": {
            "name": "test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "description": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
        },
        "assignees": [
            {
                "id": 3612771,
                "name": "Fabio Rosado",
                "username": "FabioRosado",
                "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
                "email": "[REDACTED]",
            }
        ],
    }
    assert connector


@pytest.mark.asyncio
async def test_mr_labeled_event(opsdroid, caplog):
    connector = ConnectorGitlab({}, opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "object_kind": "merge_request",
        "event_type": "merge_request",
        "user": {
            "id": 3612771,
            "name": "Fabio Rosado",
            "username": "FabioRosado",
            "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
            "email": "[REDACTED]",
        },
        "project": {
            "id": 30456730,
            "name": "test-project",
            "description": "",
            "web_url": "https://gitlab.com/FabioRosado/test-project",
            "avatar_url": None,
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "namespace": "Fabio Rosado",
            "visibility_level": 0,
            "path_with_namespace": "FabioRosado/test-project",
            "default_branch": "main",
            "ci_config_path": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "http_url": "https://gitlab.com/FabioRosado/test-project.git",
        },
        "object_attributes": {
            "assignee_id": 3612771,
            "author_id": 3612771,
            "created_at": "2021-11-07 18:14:50 UTC",
            "description": "",
            "head_pipeline_id": None,
            "id": 124957728,
            "iid": 1,
            "last_edited_at": None,
            "last_edited_by_id": None,
            "merge_commit_sha": None,
            "merge_error": None,
            "merge_params": {"force_remove_source_branch": "1"},
            "merge_status": "can_be_merged",
            "merge_user_id": None,
            "merge_when_pipeline_succeeds": False,
            "milestone_id": None,
            "source_branch": "test",
            "source_project_id": 30456730,
            "state_id": 1,
            "target_branch": "main",
            "target_project_id": 30456730,
            "time_estimate": 0,
            "title": "Test MR",
            "updated_at": "2021-11-07 18:16:12 UTC",
            "updated_by_id": 3612771,
            "url": "https://gitlab.com/FabioRosado/test-project/-/merge_requests/1",
            "source": {
                "id": 30456730,
                "name": "test-project",
                "description": "",
                "web_url": "https://gitlab.com/FabioRosado/test-project",
                "avatar_url": None,
                "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
                "namespace": "Fabio Rosado",
                "visibility_level": 0,
                "path_with_namespace": "FabioRosado/test-project",
                "default_branch": "main",
                "ci_config_path": "",
                "homepage": "https://gitlab.com/FabioRosado/test-project",
                "url": "git@gitlab.com:FabioRosado/test-project.git",
                "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "http_url": "https://gitlab.com/FabioRosado/test-project.git",
            },
            "target": {
                "id": 30456730,
                "name": "test-project",
                "description": "",
                "web_url": "https://gitlab.com/FabioRosado/test-project",
                "avatar_url": None,
                "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
                "namespace": "Fabio Rosado",
                "visibility_level": 0,
                "path_with_namespace": "FabioRosado/test-project",
                "default_branch": "main",
                "ci_config_path": "",
                "homepage": "https://gitlab.com/FabioRosado/test-project",
                "url": "git@gitlab.com:FabioRosado/test-project.git",
                "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "http_url": "https://gitlab.com/FabioRosado/test-project.git",
            },
            "last_commit": {
                "id": "32117d8dffa9c0788c7a1842df1333772dc6aaf6",
                "message": "Add test\n",
                "title": "Add test",
                "timestamp": "2021-11-07T18:14:28+00:00",
                "url": "https://gitlab.com/FabioRosado/test-project/-/commit/32117d8dffa9c0788c7a1842df1333772dc6aaf6",
                "author": {"name": "FabioRosado", "email": "fabioglrosado@gmail.com"},
            },
            "work_in_progress": False,
            "total_time_spent": 0,
            "time_change": 0,
            "human_total_time_spent": None,
            "human_time_change": None,
            "human_time_estimate": None,
            "assignee_ids": [3612771],
            "state": "opened",
            "action": "update",
        },
        "labels": [
            {
                "id": 22478741,
                "title": "test-label",
                "color": "#009966",
                "project_id": 30456730,
                "created_at": "2021-11-07 18:10:43 UTC",
                "updated_at": "2021-11-07 18:10:43 UTC",
                "template": False,
                "description": None,
                "type": "ProjectLabel",
                "group_id": None,
            }
        ],
        "changes": {
            "updated_at": {
                "previous": "2021-11-07 18:16:12 UTC",
                "current": "2021-11-07 18:16:12 UTC",
            },
            "updated_by_id": {"previous": None, "current": 3612771},
            "labels": {
                "previous": [],
                "current": [
                    {
                        "id": 22478741,
                        "title": "test-label",
                        "color": "#009966",
                        "project_id": 30456730,
                        "created_at": "2021-11-07 18:10:43 UTC",
                        "updated_at": "2021-11-07 18:10:43 UTC",
                        "template": False,
                        "description": None,
                        "type": "ProjectLabel",
                        "group_id": None,
                    }
                ],
            },
        },
        "repository": {
            "name": "test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "description": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
        },
        "assignees": [
            {
                "id": 3612771,
                "name": "Fabio Rosado",
                "username": "FabioRosado",
                "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
                "email": "[REDACTED]",
            }
        ],
    }

    assert connector


@pytest.mark.asyncio
async def test_mr_changed_tag_event(opsdroid, caplog):
    connector = ConnectorGitlab({}, opsdroid)

    mock_request = amock.CoroutineMock()
    mock_request.json = amock.CoroutineMock()
    mock_request.json.return_value = {
        "object_kind": "merge_request",
        "event_type": "merge_request",
        "user": {
            "id": 3612771,
            "name": "Fabio Rosado",
            "username": "FabioRosado",
            "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
            "email": "[REDACTED]",
        },
        "project": {
            "id": 30456730,
            "name": "test-project",
            "description": "",
            "web_url": "https://gitlab.com/FabioRosado/test-project",
            "avatar_url": None,
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "namespace": "Fabio Rosado",
            "visibility_level": 0,
            "path_with_namespace": "FabioRosado/test-project",
            "default_branch": "main",
            "ci_config_path": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "http_url": "https://gitlab.com/FabioRosado/test-project.git",
        },
        "object_attributes": {
            "assignee_id": 3612771,
            "author_id": 3612771,
            "created_at": "2021-11-07 18:14:50 UTC",
            "description": "",
            "head_pipeline_id": None,
            "id": 124957728,
            "iid": 1,
            "last_edited_at": None,
            "last_edited_by_id": None,
            "merge_commit_sha": None,
            "merge_error": None,
            "merge_params": {"force_remove_source_branch": "1"},
            "merge_status": "can_be_merged",
            "merge_user_id": None,
            "merge_when_pipeline_succeeds": False,
            "milestone_id": None,
            "source_branch": "test",
            "source_project_id": 30456730,
            "state_id": 1,
            "target_branch": "main",
            "target_project_id": 30456730,
            "time_estimate": 0,
            "title": "Test MR",
            "updated_at": "2021-11-07 18:17:29 UTC",
            "updated_by_id": 3612771,
            "url": "https://gitlab.com/FabioRosado/test-project/-/merge_requests/1",
            "source": {
                "id": 30456730,
                "name": "test-project",
                "description": "",
                "web_url": "https://gitlab.com/FabioRosado/test-project",
                "avatar_url": None,
                "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
                "namespace": "Fabio Rosado",
                "visibility_level": 0,
                "path_with_namespace": "FabioRosado/test-project",
                "default_branch": "main",
                "ci_config_path": "",
                "homepage": "https://gitlab.com/FabioRosado/test-project",
                "url": "git@gitlab.com:FabioRosado/test-project.git",
                "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "http_url": "https://gitlab.com/FabioRosado/test-project.git",
            },
            "target": {
                "id": 30456730,
                "name": "test-project",
                "description": "",
                "web_url": "https://gitlab.com/FabioRosado/test-project",
                "avatar_url": None,
                "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
                "namespace": "Fabio Rosado",
                "visibility_level": 0,
                "path_with_namespace": "FabioRosado/test-project",
                "default_branch": "main",
                "ci_config_path": "",
                "homepage": "https://gitlab.com/FabioRosado/test-project",
                "url": "git@gitlab.com:FabioRosado/test-project.git",
                "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "http_url": "https://gitlab.com/FabioRosado/test-project.git",
            },
            "last_commit": {
                "id": "32117d8dffa9c0788c7a1842df1333772dc6aaf6",
                "message": "Add test\n",
                "title": "Add test",
                "timestamp": "2021-11-07T18:14:28+00:00",
                "url": "https://gitlab.com/FabioRosado/test-project/-/commit/32117d8dffa9c0788c7a1842df1333772dc6aaf6",
                "author": {"name": "FabioRosado", "email": "fabioglrosado@gmail.com"},
            },
            "work_in_progress": False,
            "total_time_spent": 0,
            "time_change": 0,
            "human_total_time_spent": None,
            "human_time_change": None,
            "human_time_estimate": None,
            "assignee_ids": [3612771],
            "state": "opened",
            "action": "update",
        },
        "labels": [
            {
                "id": 22478750,
                "title": "blah",
                "color": "#ff0000",
                "project_id": 30456730,
                "created_at": "2021-11-07 18:17:22 UTC",
                "updated_at": "2021-11-07 18:17:22 UTC",
                "template": False,
                "description": None,
                "type": "ProjectLabel",
                "group_id": None,
            }
        ],
        "changes": {
            "labels": {
                "previous": [
                    {
                        "id": 22478741,
                        "title": "test-label",
                        "color": "#009966",
                        "project_id": 30456730,
                        "created_at": "2021-11-07 18:10:43 UTC",
                        "updated_at": "2021-11-07 18:10:43 UTC",
                        "template": False,
                        "description": None,
                        "type": "ProjectLabel",
                        "group_id": None,
                    }
                ],
                "current": [
                    {
                        "id": 22478750,
                        "title": "blah",
                        "color": "#ff0000",
                        "project_id": 30456730,
                        "created_at": "2021-11-07 18:17:22 UTC",
                        "updated_at": "2021-11-07 18:17:22 UTC",
                        "template": False,
                        "description": None,
                        "type": "ProjectLabel",
                        "group_id": None,
                    }
                ],
            }
        },
        "repository": {
            "name": "test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "description": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
        },
        "assignees": [
            {
                "id": 3612771,
                "name": "Fabio Rosado",
                "username": "FabioRosado",
                "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
                "email": "[REDACTED]",
            }
        ],
    }

    assert connector


@pytest.mark.asyncio
async def test_mr_approved_event(opsdroid, caplog):
    connector = ConnectorGitlab({}, opsdroid)

    event = await connector.handle_merge_request_event(
        labels=["blah"],
        project_name="test-project",
        username="FabioRosado",
        url="https://gitlab.com/FabioRosado/test-project/-/merge_requests/1",
        title="Test MR",
        description="Test description",
        action="approved",
    )

    assert isinstance(event, gitlab_events.MRApproved)
    assert event.user == "FabioRosado"
    assert event.title == "Test MR"
    assert event.project == "test-project"
    assert event.description == "Test description"
    assert event.url == "https://gitlab.com/FabioRosado/test-project/-/merge_requests/1"
    assert isinstance(event.labels, list)
    assert "blah" in event.labels


@pytest.mark.asyncio
async def test_get_labels(opsdroid):
    payload = {
        "object_kind": "merge_request",
        "event_type": "merge_request",
        "user": {
            "id": 3612771,
            "name": "Fabio Rosado",
            "username": "FabioRosado",
            "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
            "email": "[REDACTED]",
        },
        "project": {
            "id": 30456730,
            "name": "test-project",
            "description": "",
            "web_url": "https://gitlab.com/FabioRosado/test-project",
            "avatar_url": None,
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "namespace": "Fabio Rosado",
            "visibility_level": 0,
            "path_with_namespace": "FabioRosado/test-project",
            "default_branch": "main",
            "ci_config_path": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "http_url": "https://gitlab.com/FabioRosado/test-project.git",
        },
        "object_attributes": {
            "assignee_id": 3612771,
            "author_id": 3612771,
            "created_at": "2021-11-07 18:14:50 UTC",
            "description": "Test description",
            "head_pipeline_id": None,
            "id": 124957728,
            "iid": 1,
            "last_edited_at": None,
            "last_edited_by_id": None,
            "merge_commit_sha": None,
            "merge_error": None,
            "merge_params": {"force_remove_source_branch": "1"},
            "merge_status": "can_be_merged",
            "merge_user_id": None,
            "merge_when_pipeline_succeeds": False,
            "milestone_id": None,
            "source_branch": "test",
            "source_project_id": 30456730,
            "state_id": 1,
            "target_branch": "main",
            "target_project_id": 30456730,
            "time_estimate": 0,
            "title": "Test MR",
            "updated_at": "2021-11-07 20:12:18 UTC",
            "updated_by_id": 3612771,
            "url": "https://gitlab.com/FabioRosado/test-project/-/merge_requests/1",
            "source": {
                "id": 30456730,
                "name": "test-project",
                "description": "",
                "web_url": "https://gitlab.com/FabioRosado/test-project",
                "avatar_url": None,
                "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
                "namespace": "Fabio Rosado",
                "visibility_level": 0,
                "path_with_namespace": "FabioRosado/test-project",
                "default_branch": "main",
                "ci_config_path": "",
                "homepage": "https://gitlab.com/FabioRosado/test-project",
                "url": "git@gitlab.com:FabioRosado/test-project.git",
                "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "http_url": "https://gitlab.com/FabioRosado/test-project.git",
            },
            "target": {
                "id": 30456730,
                "name": "test-project",
                "description": "",
                "web_url": "https://gitlab.com/FabioRosado/test-project",
                "avatar_url": None,
                "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
                "namespace": "Fabio Rosado",
                "visibility_level": 0,
                "path_with_namespace": "FabioRosado/test-project",
                "default_branch": "main",
                "ci_config_path": "",
                "homepage": "https://gitlab.com/FabioRosado/test-project",
                "url": "git@gitlab.com:FabioRosado/test-project.git",
                "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "http_url": "https://gitlab.com/FabioRosado/test-project.git",
            },
            "last_commit": {
                "id": "fcad4dba40a75eb106df49e90dd7eb162ac95589",
                "message": "Add new commit\n",
                "title": "Add new commit",
                "timestamp": "2021-11-07T18:19:26+00:00",
                "url": "https://gitlab.com/FabioRosado/test-project/-/commit/fcad4dba40a75eb106df49e90dd7eb162ac95589",
                "author": {"name": "FabioRosado", "email": "fabioglrosado@gmail.com"},
            },
            "work_in_progress": False,
            "total_time_spent": 0,
            "time_change": 0,
            "human_total_time_spent": None,
            "human_time_change": None,
            "human_time_estimate": None,
            "assignee_ids": [3612771],
            "state": "opened",
            "action": "approved",
        },
        "labels": [
            {
                "id": 22478750,
                "title": "blah",
                "color": "#ff0000",
                "project_id": 30456730,
                "created_at": "2021-11-07 18:17:22 UTC",
                "updated_at": "2021-11-07 18:17:22 UTC",
                "template": False,
                "description": None,
                "type": "ProjectLabel",
                "group_id": None,
            }
        ],
        "changes": {},
        "repository": {
            "name": "test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "description": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
        },
        "assignees": [
            {
                "id": 3612771,
                "name": "Fabio Rosado",
                "username": "FabioRosado",
                "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
                "email": "[REDACTED]",
            }
        ],
    }

    connector = ConnectorGitlab({}, opsdroid)

    labels = await connector.get_labels(payload)

    assert "blah" in labels
    assert isinstance(labels, list)

    labels = await connector.get_labels({})
    assert isinstance(labels, list)
    assert labels == []


@pytest.mark.asyncio
async def test_get_project_name(opsdroid):
    payload = {
        "object_kind": "merge_request",
        "event_type": "merge_request",
        "user": {
            "id": 3612771,
            "name": "Fabio Rosado",
            "username": "FabioRosado",
            "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
            "email": "[REDACTED]",
        },
        "project": {
            "id": 30456730,
            "name": "test-project",
            "description": "",
            "web_url": "https://gitlab.com/FabioRosado/test-project",
            "avatar_url": None,
            "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
            "namespace": "Fabio Rosado",
            "visibility_level": 0,
            "path_with_namespace": "FabioRosado/test-project",
            "default_branch": "main",
            "ci_config_path": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
            "http_url": "https://gitlab.com/FabioRosado/test-project.git",
        },
        "object_attributes": {
            "assignee_id": 3612771,
            "author_id": 3612771,
            "created_at": "2021-11-07 18:14:50 UTC",
            "description": "Test description",
            "head_pipeline_id": None,
            "id": 124957728,
            "iid": 1,
            "last_edited_at": None,
            "last_edited_by_id": None,
            "merge_commit_sha": None,
            "merge_error": None,
            "merge_params": {"force_remove_source_branch": "1"},
            "merge_status": "can_be_merged",
            "merge_user_id": None,
            "merge_when_pipeline_succeeds": False,
            "milestone_id": None,
            "source_branch": "test",
            "source_project_id": 30456730,
            "state_id": 1,
            "target_branch": "main",
            "target_project_id": 30456730,
            "time_estimate": 0,
            "title": "Test MR",
            "updated_at": "2021-11-07 20:12:18 UTC",
            "updated_by_id": 3612771,
            "url": "https://gitlab.com/FabioRosado/test-project/-/merge_requests/1",
            "source": {
                "id": 30456730,
                "name": "test-project",
                "description": "",
                "web_url": "https://gitlab.com/FabioRosado/test-project",
                "avatar_url": None,
                "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
                "namespace": "Fabio Rosado",
                "visibility_level": 0,
                "path_with_namespace": "FabioRosado/test-project",
                "default_branch": "main",
                "ci_config_path": "",
                "homepage": "https://gitlab.com/FabioRosado/test-project",
                "url": "git@gitlab.com:FabioRosado/test-project.git",
                "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "http_url": "https://gitlab.com/FabioRosado/test-project.git",
            },
            "target": {
                "id": 30456730,
                "name": "test-project",
                "description": "",
                "web_url": "https://gitlab.com/FabioRosado/test-project",
                "avatar_url": None,
                "git_ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "git_http_url": "https://gitlab.com/FabioRosado/test-project.git",
                "namespace": "Fabio Rosado",
                "visibility_level": 0,
                "path_with_namespace": "FabioRosado/test-project",
                "default_branch": "main",
                "ci_config_path": "",
                "homepage": "https://gitlab.com/FabioRosado/test-project",
                "url": "git@gitlab.com:FabioRosado/test-project.git",
                "ssh_url": "git@gitlab.com:FabioRosado/test-project.git",
                "http_url": "https://gitlab.com/FabioRosado/test-project.git",
            },
            "last_commit": {
                "id": "fcad4dba40a75eb106df49e90dd7eb162ac95589",
                "message": "Add new commit\n",
                "title": "Add new commit",
                "timestamp": "2021-11-07T18:19:26+00:00",
                "url": "https://gitlab.com/FabioRosado/test-project/-/commit/fcad4dba40a75eb106df49e90dd7eb162ac95589",
                "author": {"name": "FabioRosado", "email": "fabioglrosado@gmail.com"},
            },
            "work_in_progress": False,
            "total_time_spent": 0,
            "time_change": 0,
            "human_total_time_spent": None,
            "human_time_change": None,
            "human_time_estimate": None,
            "assignee_ids": [3612771],
            "state": "opened",
            "action": "approved",
        },
        "labels": [
            {
                "id": 22478750,
                "title": "blah",
                "color": "#ff0000",
                "project_id": 30456730,
                "created_at": "2021-11-07 18:17:22 UTC",
                "updated_at": "2021-11-07 18:17:22 UTC",
                "template": False,
                "description": None,
                "type": "ProjectLabel",
                "group_id": None,
            }
        ],
        "changes": {},
        "repository": {
            "name": "test-project",
            "url": "git@gitlab.com:FabioRosado/test-project.git",
            "description": "",
            "homepage": "https://gitlab.com/FabioRosado/test-project",
        },
        "assignees": [
            {
                "id": 3612771,
                "name": "Fabio Rosado",
                "username": "FabioRosado",
                "avatar_url": "https://secure.gravatar.com/avatar/c13aab50cd7f21b8c340136ac4ce515a?s=80&d=identicon",
                "email": "[REDACTED]",
            }
        ],
    }

    connector = ConnectorGitlab({}, opsdroid)

    project_name = await connector.get_project_name(payload)

    assert project_name == "test-project"

    project_name = await connector.get_project_name({})

    assert project_name == ""

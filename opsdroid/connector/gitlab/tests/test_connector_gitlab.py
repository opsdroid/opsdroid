import asyncio
import logging
from pathlib import Path

import asynctest.mock as amock
import opsdroid.connector.gitlab.events as gitlab_events
import pytest
from opsdroid.connector.gitlab import ConnectorGitlab
from opsdroid.const import GITLAB_API_ENDPOINT
from opsdroid.events import Message
from opsdroid.matchers import match_event
from opsdroid.testing import call_endpoint, running_opsdroid


@pytest.fixture
async def connector(opsdroid, mock_api_obj):
    opsdroid.config["connectors"] = {"gitlab": {"webhook-token": "secret-stuff!"}}

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
async def test_gitlab_webhook_handler_excepion(caplog):
    caplog.set_level(logging.DEBUG)
    connector = ConnectorGitlab({"name": "gitlab"})
    mocked_request = amock.CoroutineMock()
    mocked_request.json.side_effect = Exception()

    resp = await connector.gitlab_webhook_handler(mocked_request)

    assert resp.status == 400
    assert "Unable to get JSON from request" in caplog.text


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

    @match_event(gitlab_events.GitlabIssueCreated)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/issues/1"
        target = f"{GITLAB_API_ENDPOINT}/projects/30456730/issues/1"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.target == target
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "New test issue"
        assert event.description == "Test description"
        assert event.labels == ["test-label"]
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
async def test_issue_label_updated(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.GitlabIssueLabeled)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/issues/1"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "New test issue"
        assert event.description == "This should have been filled"
        assert event.labels == ["test-label"]
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
            data=get_webhook_payload("issue_label_update.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_issue_labeled(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.GitlabIssueLabeled)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/issues/2"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "test"
        assert event.description == ""
        assert event.labels == ["blah"]
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
            data=get_webhook_payload("issue_labeled.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_issue_edited(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.GitlabIssueEdited)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/issues/1"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "New test issue"
        assert event.description == "This should have been filled"
        assert event.labels == ["test-label"]
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
            data=get_webhook_payload("issue_message_edited.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_generic_issue(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.GenericIssueEvent)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/issues/1"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "New test issue"
        assert event.description == "This should have been filled"
        assert event.labels == ["test-label"]
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
            data=get_webhook_payload("generic_issue.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_no_token_returns_401(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.GitlabIssueCreated)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/issues/1"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "New test issue"
        assert event.description == "Test description"
        assert event.labels == ["test-label"]
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

    @match_event(gitlab_events.GitlabIssueClosed)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/issues/1"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "New test issue"
        assert event.description == "This should have been filled"
        assert event.labels == ["test-label"]
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
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "Diaspora"
        assert event.user == "jsmith"
        assert event.title is None
        assert event.description is None
        assert event.labels == []
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


@pytest.mark.asyncio
async def test_bad_json_file(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.DEBUG)

    @match_event(gitlab_events.GenericGitlabEvent)
    async def test_skill(opsdroid, config, event):
        url = "http://example.com/mike/diaspora"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "Diaspora"
        assert event.user == "jsmith"
        assert event.title is None
        assert event.description is None
        assert event.labels == []
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
            data=get_webhook_payload("bad_json.json"),
        )

        assert resp.status == 400
        assert "Unable to decode json" in caplog.text
        assert "Test skill complete" not in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_mr_label_update_event(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.MRLabeled)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/merge_requests/1"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "Test MR"
        assert event.description == ""
        assert event.labels == ["blah"]
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
            data=get_webhook_payload("mr_label_update.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_mr_opened_event(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.MRCreated)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/merge_requests/1"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "Test MR"
        assert event.description == ""
        assert event.labels == []
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
            data=get_webhook_payload("mr_opened.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_mr_merged_event(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.MRMerged)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/merge_requests/1"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "Test MR"
        assert event.description == ""
        assert event.labels == ["blah"]
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
            data=get_webhook_payload("mr_merged.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_mr_approved_event(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.MRApproved)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/merge_requests/1"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == "Test MR"
        assert event.description == ""
        assert event.labels == ["blah"]
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
            data=get_webhook_payload("mr_approved.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_mr_closed_event(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.MRClosed)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/merge_requests/2"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == 'Revert Merge branch "test" into "main"'
        assert event.description == "This reverts merge request !1"
        assert event.labels == []
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
            data=get_webhook_payload("mr_closed.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


@pytest.mark.asyncio
async def test_mr_generic_event(opsdroid, connector, mock_api, caplog):
    caplog.set_level(logging.INFO)

    @match_event(gitlab_events.GenericMREvent)
    async def test_skill(opsdroid, config, event):
        url = "https://gitlab.com/FabioRosado/test-project/-/merge_requests/2"
        assert event.connector.name == "gitlab"
        assert event.url == url
        assert event.project == "test-project"
        assert event.user == "FabioRosado"
        assert event.title == 'Revert Merge branch "test" into "main"'
        assert event.description == "This reverts merge request !1"
        assert event.labels == []
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
            data=get_webhook_payload("generic_mr.json"),
        )

        assert resp.status == 200
        assert "Test skill complete" in caplog.text
        assert "Exception when running skill" not in caplog.text


ISSUE_TARGET = "FabioRosado/test-project/-/issues/1"


@pytest.mark.asyncio
async def test_send_message(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorGitlab(
        {"webhook-token": "secret-stuff!", "token": "my-token"},
        opsdroid=opsdroid,
    )

    response = amock.Mock()
    response.status = 201

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        assert opsdroid.__class__.instances

        test_message = Message(
            text="This is a test",
            user="opsdroid",
            target=ISSUE_TARGET,
            connector=connector,
        )

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        result = await connector.send(test_message)

        assert patched_request.called
        assert "Responding via Gitlab" in caplog.text
        assert "Message 'This is a test' sent to GitLab" in caplog.text
        assert result is True


@pytest.mark.asyncio
async def test_send_message_bad_status(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorGitlab(
        {"webhook-token": "secret-stuff!", "token": "my-token"},
        opsdroid=opsdroid,
    )

    response = amock.Mock()
    response.status = 422

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        assert opsdroid.__class__.instances

        test_message = Message(
            text="This is a test",
            user="opsdroid",
            target=ISSUE_TARGET,
            connector=connector,
        )

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        result = await connector.send(test_message)

        assert patched_request.called
        assert "Responding via Gitlab" in caplog.text
        assert "Unable to send 'This is a test' to GitLab." in caplog.text
        assert result is False


@pytest.mark.asyncio
async def test_send_message_no_token(opsdroid, caplog):
    caplog.set_level(logging.DEBUG)

    connector = ConnectorGitlab(
        {"webhook-token": "secret-stuff!"},
        opsdroid=opsdroid,
    )

    response = amock.Mock()

    with amock.patch(
        "aiohttp.ClientSession.post", new=amock.CoroutineMock()
    ) as patched_request:
        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        assert opsdroid.__class__.instances

        test_message = Message(
            text="This is a test",
            user="opsdroid",
            target=ISSUE_TARGET,
            connector=connector,
        )

        patched_request.return_value = asyncio.Future()
        patched_request.return_value.set_result(response)

        result = await connector.send(test_message)

        assert not patched_request.called
        assert "Unable to reply to GitLab" in caplog.text
        assert result is False

"""Test the opsdroid matcher decorators."""

import pytest

import asyncio
import aiohttp.web

from aiohttp.test_utils import make_mocked_request

from opsdroid.cli.start import configure_lang
from opsdroid.web import Web
from opsdroid import matchers

configure_lang({})


async def get_mock_skill():
    async def mocked_skill(opsdroid, config, message):
        pass

    return mocked_skill


async def get_mock_web_skill():
    async def mocked_web_skill(opsdroid, config, message):
        return aiohttp.web.Response(body=b"custom response", status=200)

    return mocked_web_skill


@pytest.mark.asyncio
async def test_match_regex(opsdroid):
    regex = r"(.*)"
    decorator = matchers.match_regex(regex)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    assert len(opsdroid.skills) == 1
    assert opsdroid.skills[0].matchers[0]["regex"]["expression"] == regex
    assert asyncio.iscoroutinefunction(opsdroid.skills[0])


@pytest.mark.asyncio
async def test_match_dialogflow(opsdroid):
    action = "myaction"
    decorator = matchers.match_dialogflow_action(action)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    assert len(opsdroid.skills) == 1
    assert opsdroid.skills[0].matchers[0]["dialogflow_action"] == action

    assert asyncio.iscoroutinefunction(opsdroid.skills[0])
    intent = "myIntent"
    decorator = matchers.match_dialogflow_intent(intent)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    assert len(opsdroid.skills) == 2
    assert opsdroid.skills[1].matchers[0]["dialogflow_intent"] == intent
    assert asyncio.iscoroutinefunction(opsdroid.skills[1])


@pytest.mark.asyncio
async def test_match_luisai(opsdroid):
    intent = "myIntent"
    decorator = matchers.match_luisai_intent(intent)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    assert len(opsdroid.skills) == 1
    assert opsdroid.skills[0].matchers[0]["luisai_intent"] == intent
    assert asyncio.iscoroutinefunction(opsdroid.skills[0]) is True


@pytest.mark.asyncio
async def test_match_watson(opsdroid):
    intent = "myIntent"
    decorator = matchers.match_watson(intent)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    assert len(opsdroid.skills) == 1
    assert opsdroid.skills[0].matchers[0]["watson_intent"] == intent
    assert asyncio.iscoroutinefunction(opsdroid.skills[0]) is True


@pytest.mark.asyncio
async def test_match_witai(opsdroid):
    intent = "myIntent"
    decorator = matchers.match_witai(intent)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    assert len(opsdroid.skills) == 1
    assert opsdroid.skills[0].matchers[0]["witai_intent"] == intent
    assert asyncio.iscoroutinefunction(opsdroid.skills[0]) is True


@pytest.mark.asyncio
async def test_match_rasanu(opsdroid):
    intent = "myIntent"
    decorator = matchers.match_rasanlu(intent)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    assert len(opsdroid.skills) == 1
    assert opsdroid.skills[0].matchers[0]["rasanlu_intent"] == intent
    assert asyncio.iscoroutinefunction(opsdroid.skills[0])


@pytest.mark.asyncio
async def test_match_recastai(opsdroid, caplog):
    intent = "myIntent"
    decorator = matchers.match_recastai(intent)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    assert len(opsdroid.skills) == 1
    assert opsdroid.skills[0].matchers[0]["sapcai_intent"] == intent
    assert asyncio.iscoroutinefunction(opsdroid.skills[0])


@pytest.mark.asyncio
async def test_match_crontab(opsdroid):
    crontab = "* * * * *"
    decorator = matchers.match_crontab(crontab)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    assert len(opsdroid.skills) == 1
    assert opsdroid.skills[0].matchers[0]["crontab"] == crontab
    assert asyncio.iscoroutinefunction(opsdroid.skills[0])


@pytest.mark.asyncio
async def test_match_webhook(opsdroid, mocker):
    opsdroid.loader.current_import_config = {"name": "testhook"}
    opsdroid.web_server = Web(opsdroid)
    opsdroid.web_server.web_app = mocker.MagicMock()
    webhook = "test"
    decorator = matchers.match_webhook(webhook)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    opsdroid.skills[0].config = {"name": "mockedskill"}
    opsdroid.web_server.setup_webhooks(opsdroid.skills)
    assert len(opsdroid.skills) == 1
    assert opsdroid.skills[0].matchers[0]["webhook"] == webhook
    assert asyncio.iscoroutinefunction(opsdroid.skills[0])
    assert opsdroid.web_server.web_app.router.add_post.call_count == 2


@pytest.mark.asyncio
async def test_match_webhook_response(opsdroid, mocker):
    opsdroid.loader.current_import_config = {"name": "testhook"}
    opsdroid.web_server = Web(opsdroid)
    opsdroid.web_server.web_app = mocker.MagicMock()
    webhook = "test"
    decorator = matchers.match_webhook(webhook)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    opsdroid.skills[0].config = {"name": "mockedskill"}
    opsdroid.web_server.setup_webhooks(opsdroid.skills)
    postcalls, _ = opsdroid.web_server.web_app.router.add_post.call_args_list[0]
    wrapperfunc = postcalls[1]
    webhookresponse = await wrapperfunc(None)
    assert isinstance(webhookresponse, aiohttp.web.Response)


@pytest.mark.asyncio
async def test_match_webhook_response_with_authorization_failure(opsdroid, mocker):
    opsdroid.loader.current_import_config = {"name": "testhook"}
    opsdroid.config["web"] = {"webhook-token": "aabbccddeeff"}
    opsdroid.web_server = Web(opsdroid)
    opsdroid.web_server.web_app = mocker.MagicMock()
    webhook = "test"
    decorator = matchers.match_webhook(webhook)
    opsdroid.skills.append(decorator(await get_mock_skill()))
    opsdroid.skills[0].config = {"name": "mockedskill"}
    opsdroid.web_server.setup_webhooks(opsdroid.skills)
    postcalls, _ = opsdroid.web_server.web_app.router.add_post.call_args_list[0]
    wrapperfunc = postcalls[1]
    webhookresponse = await wrapperfunc(
        make_mocked_request(
            "POST", postcalls[0], headers={"Authorization": "Bearer wwxxyyzz"}
        )
    )
    assert isinstance(webhookresponse, aiohttp.web.Response)


@pytest.mark.asyncio
async def test_match_webhook_custom_response(opsdroid, mocker):
    opsdroid.loader.current_import_config = {"name": "testhook"}
    opsdroid.web_server = Web(opsdroid)
    opsdroid.web_server.web_app = mocker.MagicMock()
    webhook = "test"
    decorator = matchers.match_webhook(webhook)
    opsdroid.skills.append(decorator(await get_mock_web_skill()))
    opsdroid.skills[0].config = {"name": "mockedskill"}
    opsdroid.web_server.setup_webhooks(opsdroid.skills)
    postcalls, _ = opsdroid.web_server.web_app.router.add_post.call_args_list[0]
    wrapperfunc = postcalls[1]
    webhookresponse = await wrapperfunc(None)
    assert isinstance(webhookresponse, aiohttp.web.Response)
    assert webhookresponse.body == b"custom response"

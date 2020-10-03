import asynctest.mock as amock
import pytest

from opsdroid.matchers import match_watson
from opsdroid.events import Message
from opsdroid.parsers import watson

from opsdroid.connector import Connector
import ibm_cloud_sdk_core
import ibm_watson
from ibm_watson import ApiException


async def getMockSkill():
    async def mockedskill(opsdroid, config, message):
        pass

    mockedskill.config = {}
    return mockedskill


@pytest.mark.asyncio
async def test_get_all_entities():
    entities = [
        {
            "entity": "sys-number",
            "location": [24, 26],
            "value": "18",
            "confidence": 1,
        },
        {
            "entity": "sys-date",
            "location": [24, 32],
            "value": "2019-10-18",
            "confidence": 1,
        },
        {
            "entity": "sys-number",
            "location": [27, 29],
            "value": "10",
            "confidence": 1,
        },
        {
            "entity": "sys-number",
            "location": [30, 32],
            "value": "19",
            "confidence": 1,
        },
        {
            "entity": "sys-time",
            "location": [33, 39],
            "value": "15:00:00",
            "confidence": 1,
        },
    ]

    entities_dict = await watson.get_all_entities(entities)

    assert entities_dict == {
        "sys-number": ["18", "10", "19"],
        "sys-date": ["2019-10-18"],
        "sys-time": ["15:00:00"],
    }


@pytest.mark.asyncio
async def test_get_session_id():
    config = {
        "name": "watson",
        "token": "test",
        "gateway": "gateway",
        "min-score": 0.3,
        "assistant-id": "test",
    }
    result = amock.Mock()
    service = amock.MagicMock()

    result.return_value = {"session_id": "test123"}

    service.create_session.return_value.set_result(result)

    await watson.get_session_id(service, config)

    assert "session-id" in config


@pytest.mark.asyncio
async def test_call_watson(opsdroid, caplog, mocker):
    opsdroid = amock.CoroutineMock()
    mock_connector = Connector({}, opsdroid=opsdroid)
    message = Message("Hello", "user", "default", mock_connector)
    config = {
        "name": "watson",
        "token": "test",
        "gateway": "gateway",
        "min-score": 0.3,
        "assistant-id": "test",
        "session-id": "12ndior2kld",
    }
    result = amock.Mock()
    result.json = amock.CoroutineMock()
    result.json.return_value = {
        "output": {
            "generic": [{"response_type": "text", "text": "Hey hows it going?"}],
            "intents": [{"intent": "hello", "confidence": 1}],
            "entities": [
                {
                    "entity": "greetings",
                    "location": [0, 2],
                    "value": "hello",
                    "confidence": 1,
                },
                {
                    "entity": "greetings",
                    "location": [0, 2],
                    "value": "hi",
                    "confidence": 1,
                },
            ],
        }
    }
    with amock.patch.object(watson, "get_session_id"):

        mocker.patch.object(ibm_cloud_sdk_core.authenticators, "IAMAuthenticator")
        mocked_service = mocker.patch.object(ibm_watson, "AssistantV2")

        mocked_service.message.get_result.return_value.set_result(result)

        await watson.call_watson(message, opsdroid, config)

        assert mocked_service.called
        assert caplog


@pytest.mark.asyncio
async def test_call_watson_import_error(opsdroid, caplog, mocker):
    opsdroid = amock.CoroutineMock()
    mock_connector = Connector({}, opsdroid=opsdroid)
    message = Message("Hello", "user", "default", mock_connector)
    config = {
        "name": "watson",
        "token": "test",
        "gateway": "gateway",
        "min-score": 0.3,
        "assistant-id": "test",
        "session-id": "12ndior2kld",
    }

    with amock.patch.object(watson, "get_session_id"):
        mocker.patch.object(
            ibm_cloud_sdk_core.authenticators,
            "IAMAuthenticator",
            side_effect=ImportError,
        )
        mocker.patch.object(ibm_watson, "AssistantV2", side_effect=ImportError)

        await watson.call_watson(message, opsdroid, config)

        assert caplog


@pytest.mark.asyncio
async def test_parse_watson(opsdroid):
    opsdroid.config["parsers"] = [
        {
            "name": "watson",
            "token": "test",
            "gateway": "gateway",
            "min-score": 0.3,
            "assistant-id": "test",
            "session-id": "12ndior2kld",
        }
    ]
    mock_skill = await getMockSkill()
    opsdroid.skills.append(match_watson("hello")(mock_skill))

    mock_connector = amock.CoroutineMock()
    message = Message("hi", "user", "default", mock_connector)

    with amock.patch.object(watson, "call_watson") as mocked_call_watson:
        mocked_call_watson.return_value = {
            "output": {
                "generic": [{"response_type": "text", "text": "Hey hows it going?"}],
                "intents": [{"intent": "hello", "confidence": 1}],
                "entities": [
                    {
                        "entity": "greetings",
                        "location": [0, 2],
                        "value": "hello",
                        "confidence": 1,
                    },
                    {
                        "entity": "greetings",
                        "location": [0, 2],
                        "value": "hi",
                        "confidence": 1,
                    },
                ],
            }
        }
        skills = await watson.parse_watson(
            opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
        )
        assert mock_skill == skills[0]["skill"]


@pytest.mark.asyncio
async def test_parse_watson_no_intent(opsdroid, caplog):
    opsdroid.config["parsers"] = [
        {
            "name": "watson",
            "token": "test",
            "gateway": "gateway",
            "min-score": 0.3,
            "assistant-id": "test",
            "session-id": "12ndior2kld",
        }
    ]
    mock_skill = await getMockSkill()
    opsdroid.skills.append(match_watson("hello")(mock_skill))

    mock_connector = amock.CoroutineMock()
    message = Message("how's the weather outside", "user", "default", mock_connector)

    with amock.patch.object(watson, "call_watson") as mocked_call_watson:
        mocked_call_watson.return_value = {
            "output": {
                "generic": [{"response_type": "text", "text": "Hey hows it going?"}],
                "intents": [],
                "entities": [],
            }
        }
        skills = await watson.parse_watson(
            opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
        )
        assert skills == []
        assert "No intent found" in caplog.text


@pytest.mark.asyncio
async def test_parse_watson_no_confidence(opsdroid, caplog):
    opsdroid.config["parsers"] = [
        {
            "name": "watson",
            "token": "test",
            "gateway": "gateway",
            "assistant-id": "test",
            "session-id": "12ndior2kld",
        }
    ]
    mock_skill = await getMockSkill()
    opsdroid.skills.append(match_watson("hello")(mock_skill))

    mock_connector = amock.CoroutineMock()
    message = Message("hi", "user", "default", mock_connector)

    with amock.patch.object(watson, "call_watson") as mocked_call_watson:
        mocked_call_watson.return_value = {
            "output": {
                "generic": [{"response_type": "text", "text": "Hey hows it going?"}],
                "intents": [{"intent": "hello"}],
                "entities": [],
            }
        }
        skills = await watson.parse_watson(
            opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
        )
        assert skills[0]["score"] == 0.0


@pytest.mark.asyncio
async def test_parse_watson_low_score(opsdroid, caplog):
    opsdroid.config["parsers"] = [
        {
            "name": "watson",
            "token": "test",
            "gateway": "gateway",
            "min-score": 0.5,
            "assistant-id": "test",
            "session-id": "12ndior2kld",
        }
    ]
    mock_skill = await getMockSkill()
    opsdroid.skills.append(match_watson("hello")(mock_skill))

    mock_connector = amock.CoroutineMock()
    message = Message("hi", "user", "default", mock_connector)

    with amock.patch.object(watson, "call_watson") as mocked_call_watson:
        mocked_call_watson.return_value = {
            "output": {
                "generic": [{"response_type": "text", "text": "Hey hows it going?"}],
                "intents": [{"intent": "hello", "confidence": 0.3}],
                "entities": [
                    {
                        "entity": "greetings",
                        "location": [0, 2],
                        "value": "hello",
                        "confidence": 1,
                    },
                    {
                        "entity": "greetings",
                        "location": [0, 2],
                        "value": "hi",
                        "confidence": 1,
                    },
                ],
            }
        }
        skills = await watson.parse_watson(
            opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
        )
        assert skills == []
        assert caplog


@pytest.mark.asyncio
async def test_parse_watson_KeyError(opsdroid, caplog):
    opsdroid.config["parsers"] = [
        {
            "name": "watson",
            "access-token": "test",
            "gateway": "gateway",
            "min-score": 0.3,
            "assistant-id": "test",
            "session-id": "12ndior2kld",
        }
    ]
    mock_skill = await getMockSkill()
    opsdroid.skills.append(match_watson("hello")(mock_skill))

    mock_connector = amock.CoroutineMock()
    message = Message("hi", "user", "default", mock_connector)

    with amock.patch.object(watson, "call_watson") as mocked_call_watson:
        mocked_call_watson.side_effect = KeyError()

        skills = await watson.parse_watson(
            opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
        )
        assert skills == []
        assert "Error" in caplog.text


@pytest.mark.asyncio
async def test_parse_watson_APIException(opsdroid, caplog):
    opsdroid.config["parsers"] = [
        {
            "name": "watson",
            "token": "test",
            "gateway": "gateway",
            "min-score": 0.3,
            "assistant-id": "test",
            "session-id": "12ndior2kld",
        }
    ]
    mock_skill = await getMockSkill()
    opsdroid.skills.append(match_watson("hello")(mock_skill))

    mock_connector = amock.CoroutineMock()
    message = Message("hi", "user", "default", mock_connector)

    with amock.patch.object(watson, "call_watson") as mocked_call_watson:
        mocked_call_watson.side_effect = ApiException(code=404, message="Not Found.")

        skills = await watson.parse_watson(
            opsdroid, opsdroid.skills, message, opsdroid.config["parsers"][0]
        )
        assert skills == []
        assert "Watson Api error" in caplog.text

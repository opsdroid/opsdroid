import pytest

import os

import aiohttp

from opsdroid.events import Message
from opsdroid.cli.start import configure_lang
from opsdroid.testing import (
    MINIMAL_CONFIG,
    ExternalAPIMockServer,
    call_endpoint,
    run_unit_test,
    running_opsdroid,
)


configure_lang({})


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.mark.asyncio
async def test_external_api_mock_server(session):
    mock_api = ExternalAPIMockServer()
    mock_api.add_response("/test", "GET", None, 200)
    mock_api.add_response("/test", "GET", None, 200)
    with pytest.raises(TypeError):
        mock_api.add_response("/fail", "NOSUCHMETHOD", None, 400)
    mock_api.add_response("/fail", "POST", None, 400)
    assert len(mock_api.responses) == 2

    assert mock_api.status == "stopped"

    async with mock_api.running():
        """A closure to test the runner."""
        assert mock_api.status == "running"
        assert mock_api.base_url == "http://localhost:8089"

        for i in range(2):
            async with session.get(f"{mock_api.base_url}/test") as resp:
                assert resp.status == 200
                assert mock_api.called("/test")
                assert mock_api.call_count("/test") == i + 1
                assert mock_api.get_request("/test").path == "/test"

        async with session.post(
            f"{mock_api.base_url}/fail", data={"hello": "world"}
        ) as resp:
            assert resp.status == 400
            assert "hello" in mock_api.get_payload("/fail")

        with pytest.raises(RuntimeError):
            mock_api.reset()

    assert mock_api.status == "stopped"

    mock_api.reset()
    assert len(mock_api.responses) == 0


@pytest.mark.parametrize("bound_address", ["localhost"], indirect=True)
@pytest.mark.asyncio
async def test_external_api_mock_server_port_in_use(bound_address, session):
    """Check retry/timeout handling when the port is in use."""
    mock_api = ExternalAPIMockServer()
    mock_api.port = bound_address[1]
    mock_api.start_timeout = 0.5  # no need to retry for 10 seconds

    mock_api.add_response("/test", "GET", None, 200)

    # linux: Errno 98 (ADDRINUSE)
    # windows: Errno 10013 (WSAEACCESS) or 10048 (WSAEADDRINUSE)
    with pytest.raises(OSError):
        async with mock_api.running():
            await session.get(f"{mock_api.base_url}/test")


@pytest.mark.asyncio
async def test_call_endpoint(opsdroid):
    await opsdroid.load(config=MINIMAL_CONFIG)

    async def test():
        resp = await call_endpoint(opsdroid, "/stats", "GET")
        assert resp.status == 200

        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "example.json"
        )
        resp = await call_endpoint(opsdroid, "/stats", "POST", data_path=data_path)
        assert resp.status == 405

        with pytest.raises(RuntimeError):
            await call_endpoint(opsdroid, "/stats", "POST")

        with pytest.raises(TypeError):
            await call_endpoint(opsdroid, "/stats", "NOSUCHMETHOD")

        return True

    assert await run_unit_test(opsdroid, test)


@pytest.mark.asyncio
async def test_run_unit_test(opsdroid):
    await opsdroid.load(config=MINIMAL_CONFIG)

    assert not opsdroid.is_running()

    async def test():
        assert opsdroid.is_running()

    assert not opsdroid.is_running()

    await run_unit_test(opsdroid, test)


@pytest.mark.asyncio
async def test_with_running_opsdroid(opsdroid):
    await opsdroid.load(config=MINIMAL_CONFIG)

    assert not opsdroid.is_running()

    async with running_opsdroid(opsdroid):
        assert opsdroid.is_running()


@pytest.mark.asyncio
async def test_mock_skill_and_connector(opsdroid):
    await opsdroid.load(config=MINIMAL_CONFIG)
    skill = opsdroid.get_skill_instance(opsdroid.skills[0])

    async def test():
        await opsdroid.parse(Message("hello", connector=opsdroid.default_connector))
        assert skill.called

    await run_unit_test(opsdroid, test)


@pytest.mark.add_response("/test", "GET")
@pytest.mark.add_response("/test2", "GET", status=500)
@pytest.mark.asyncio
async def test_mock_api_with_pytest_marks(mock_api, session):
    async with session.get(f"{mock_api.base_url}/test") as resp:
        assert resp.status == 200
        assert mock_api.called("/test")

    async with session.get(f"{mock_api.base_url}/test2") as resp:
        assert resp.status == 500
        assert mock_api.called("/test2")


@pytest.mark.add_response("/test", "GET")
@pytest.mark.add_response("/test2", "GET", status=500)
@pytest.mark.asyncio
async def test_mock_api_obj_with_pytest_marks(mock_api_obj, session):
    async with mock_api_obj.running():
        async with session.get(f"{mock_api_obj.base_url}/test") as resp:
            assert resp.status == 200
            assert mock_api_obj.called("/test")

        async with session.get(f"{mock_api_obj.base_url}/test2") as resp:
            assert resp.status == 500
            assert mock_api_obj.called("/test2")

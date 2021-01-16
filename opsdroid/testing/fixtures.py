"""Core fixtures for testing opsdroid and skills."""
import contextlib
import socket

import pytest

from opsdroid.core import OpsDroid
from opsdroid.connector import Connector

from .external_api import ExternalAPIMockServer

__all__ = ["bound_address", "get_connector", "opsdroid", "mock_api"]


@pytest.fixture(scope="session")
def get_connector(opsdroid):
    """Pytest fixture which is a factory to generate a connector."""

    def _get_connector(config={}):
        return Connector(config, opsdroid=opsdroid)

    return _get_connector


@pytest.fixture
def bound_address(request):
    """I have no idea what this does but must have a docstring."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with contextlib.suppress(socket.error):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):  # only on windows
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        if hasattr(socket, "SO_REUSEPORT"):  # not on windows
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 0)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)

    host = request.param if hasattr(request, "param") else "0.0.0.0"
    s.bind((host, 0))  # an ephemeral port
    yield s.getsockname()
    s.close()


@pytest.fixture
def opsdroid() -> OpsDroid:
    """Fixture with a plain instance of opsdroid.

    Will yield an instance of :class:`opsdroid.core.OpsDroid` which hasn't been loaded.

    """
    with OpsDroid(config={}) as opsdroid:
        yield opsdroid


@pytest.fixture
async def mock_api(request) -> ExternalAPIMockServer:
    """
    Fixture for mocking API calls to a web service.

    Will give an instance of :class:`opsdroid.testing.ExternalAPIMockServer`,
    which has been configured with any routes specified through
    ``@pytest.mark.add_response()`` decorators.

    All arguments and keyword arguments passed to ``pytest.mark.add_response``
    are passed through to `.ExternalAPIMockServer.add_response`.

    An example test would look like::

        @pytest.mark.add_response("/test", "GET")
        @pytest.mark.add_response("/test2", "GET", status=500)
        @pytest.mark.asyncio
        async def test_hello(mock_api):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{mock_api.base_url}/test") as resp:
                    assert resp.status == 200
                    assert mock_api.called("/test")

                async with session.get(f"{mock_api.base_url}/test2") as resp:
                    assert resp.status == 500
                    assert mock_api.called("/test2")

    """
    mock_api = ExternalAPIMockServer()
    markers = list(
        filter(lambda marker: marker.name == "add_response", request.node.own_markers)
    )
    if not markers:
        raise ValueError(
            "Tests using the mock_api fixture must provide request"
            " info with at least one @pytest.mark.add_response"
        )

    for marker in markers:
        mock_api.add_response(*marker.args, **marker.kwargs)

    await mock_api._start()
    yield mock_api
    await mock_api._stop()

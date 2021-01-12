"""Pytest config for all opsdroid tests."""
import pytest

import asyncio
import contextlib
import socket

from opsdroid.testing import opsdroid, mock_api  # noqa
from opsdroid.connector import Connector

from opsdroid.cli.start import configure_lang

__all__ = ["opsdroid"]

configure_lang({})


@pytest.fixture(scope="session")
def get_connector():
    def _get_connector(config={}):
        return Connector(config, opsdroid=opsdroid)

    return _get_connector


@pytest.yield_fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def bound_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with contextlib.suppress(socket.error):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):  # only on windows
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    with contextlib.suppress(socket.error):
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 0)

    s.bind(("0.0.0.0", 0))  # an ephemeral port
    yield s.getsockname()
    s.close()

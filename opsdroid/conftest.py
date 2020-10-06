"""Pytest config for all opsdroid tests."""
import pytest

import asyncio

from opsdroid.testing import opsdroid
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

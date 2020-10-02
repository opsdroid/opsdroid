"""Pytest config for all opsdroid tests."""
import pytest
from opsdroid.testing import opsdroid
from opsdroid.connector import Connector

from opsdroid.cli.start import configure_lang

__all__ = ["opsdroid"]

configure_lang({})


@pytest.fixture(scope="session")
def no_config_connector():
    return Connector({}, opsdroid=opsdroid)

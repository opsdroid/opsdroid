"""Pytest config for all opsdroid tests."""
# All global fixtures should be defined in the fixtures file
from opsdroid.testing.fixtures import *  # noqa

from opsdroid.cli.start import configure_lang

configure_lang({})

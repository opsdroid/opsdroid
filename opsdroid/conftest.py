"""Pytest config for all opsdroid tests.

This file includes definitions for any private (opsdroid-use-only) fixtures.
All public fixtures should be defined in ``opsdroid.testing.fixtures``
so that sub-projects can reuse them.
"""
from opsdroid.testing.fixtures import *  # noqa

from opsdroid.cli.start import configure_lang

configure_lang({})

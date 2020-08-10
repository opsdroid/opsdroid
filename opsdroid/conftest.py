"""Pytest config for all opsdroid tests."""
from opsdroid.testing import opsdroid

from opsdroid.cli.start import configure_lang

__all__ = ["opsdroid"]

configure_lang({})

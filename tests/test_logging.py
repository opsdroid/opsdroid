import pytest
import logging
import os
import tempfile
import contextlib

import opsdroid.logging as opsdroid
from opsdroid.cli.start import configure_lang

configure_lang({})


@pytest.fixture(scope="module")
def _tmp_dir():
    _tmp_dir = os.path.join(tempfile.gettempdir(), "opsdroid_tests")
    with contextlib.suppress(FileExistsError):
        os.makedirs(_tmp_dir, mode=0o777)
    return _tmp_dir


class TestLogging:
    """Test the logging module."""

    def test_set_logging_level(self):
        assert logging.DEBUG == opsdroid.get_logging_level("debug")
        assert logging.INFO == opsdroid.get_logging_level("info")
        assert logging.WARNING == opsdroid.get_logging_level("warning")
        assert logging.ERROR == opsdroid.get_logging_level("error")
        assert logging.CRITICAL == opsdroid.get_logging_level("critical")
        assert logging.INFO == opsdroid.get_logging_level("")

    def test_configure_no_logging(self):
        config = {"logging": {"path": False, "console": False}}
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        assert len(rootlogger.handlers) == 1
        assert isinstance(rootlogger.handlers[0], logging.StreamHandler)
        assert rootlogger.handlers[0].level == logging.CRITICAL

    def test_configure_file_logging(self, _tmp_dir):
        config = {
            "logging": {"path": os.path.join(_tmp_dir, "output.log"), "console": False}
        }
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        assert len(rootlogger.handlers), 2
        assert isinstance(rootlogger.handlers[0], logging.StreamHandler)
        assert rootlogger.handlers[0].level, logging.CRITICAL
        assert isinstance(rootlogger.handlers[1], logging.handlers.RotatingFileHandler)
        assert rootlogger.handlers[1].level == logging.INFO

    def test_configure_file_blacklist(self, _tmp_dir, caplog):
        config = {
            "logging": {
                "path": os.path.join(_tmp_dir, "output.log"),
                "console": False,
                "filter": {"blacklist": "opsdroid.logging"},
            }
        }
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        assert len(rootlogger.handlers) == 2
        assert isinstance(rootlogger.handlers[0], logging.StreamHandler)
        assert rootlogger.handlers[0].level == logging.CRITICAL
        assert isinstance(rootlogger.handlers[1], logging.handlers.RotatingFileHandler)
        assert caplog.text == ""

    def test_configure_file_logging_directory_not_exists(self, _tmp_dir, mocker):
        logmock = mocker.patch("logging.getLogger")
        mocklogger = mocker.MagicMock()
        mocklogger.handlers = [True]
        logmock.return_value = mocklogger
        config = {
            "logging": {
                "path": os.path.join(_tmp_dir, "mynonexistingdirectory", "output.log"),
                "console": False,
            }
        }
        opsdroid.configure_logging(config)

    def test_configure_console_logging(self):
        config = {"logging": {"path": False, "level": "error", "console": True}}
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        assert len(rootlogger.handlers) == 1
        assert isinstance(rootlogger.handlers[0], logging.StreamHandler)
        assert rootlogger.handlers[0].level == logging.ERROR

    def test_configure_console_blacklist(self, caplog):
        config = {
            "logging": {
                "path": False,
                "level": "error",
                "console": True,
                "filter": {"blacklist": "opsdroid"},
            }
        }
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        assert len(rootlogger.handlers) == 1
        assert isinstance(rootlogger.handlers[0], logging.StreamHandler)
        assert rootlogger.handlers[0].level == logging.ERROR
        assert caplog.text == ""

    def test_configure_console_whitelist(self):
        config = {
            "logging": {
                "path": False,
                "level": "info",
                "console": True,
                "filter": {"whitelist": "opsdroid.logging"},
            }
        }
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        assert len(rootlogger.handlers) == 1
        assert isinstance(rootlogger.handlers[0], logging.StreamHandler)
        assert rootlogger.handlers[0].level == logging.INFO

    def test_configure_extended_logging(self):
        config = {
            "logging": {
                "path": False,
                "level": "error",
                "console": True,
                "extended": True,
            }
        }
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        assert len(rootlogger.handlers) == 1
        assert isinstance(rootlogger.handlers[0], logging.StreamHandler)

    def test_configure_default_logging(self):
        config = {}
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        assert len(rootlogger.handlers), 2
        assert isinstance(rootlogger.handlers[0], logging.StreamHandler)
        assert rootlogger.handlers[0].level == logging.INFO
        assert isinstance(rootlogger.handlers[1], logging.handlers.RotatingFileHandler)
        assert rootlogger.handlers[1].level == logging.INFO


@pytest.fixture
def white_and_black_config():
    # Set up
    config = {
        "logging": {
            "path": False,
            "level": "info",
            "console": True,
            "filter": {"whitelist": ["opsdroid"], "blacklist": ["opsdroid.core"]},
        }
    }
    yield config

    # Tear down
    config = {}
    opsdroid.configure_logging(config)


class TestWhiteAndBlackFilter:
    def test_configure_whitelist_and_blacklist(self, capsys, white_and_black_config):
        opsdroid.configure_logging(white_and_black_config)
        captured = capsys.readouterr()

        log1 = "Both whitelist and blacklist filters found in configuration. "
        log2 = (
            "Only one can be used at a time - only the whitelist filter will be used."
        )

        assert log1 in captured.err
        assert log2 in captured.err

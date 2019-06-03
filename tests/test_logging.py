import unittest
import unittest.mock as mock
import logging
import os
import tempfile
import contextlib

import opsdroid.logging as opsdroid
from opsdroid.__main__ import configure_lang


class TestLogging(unittest.TestCase):
    """Test the logging module."""

    def setUp(self):
        self._tmp_dir = os.path.join(tempfile.gettempdir(), "opsdroid_tests")
        with contextlib.suppress(FileExistsError):
            os.makedirs(self._tmp_dir, mode=0o777)
        configure_lang({})

    def test_set_logging_level(self):
        self.assertEqual(logging.DEBUG, opsdroid.get_logging_level("debug"))
        self.assertEqual(logging.INFO, opsdroid.get_logging_level("info"))
        self.assertEqual(logging.WARNING, opsdroid.get_logging_level("warning"))
        self.assertEqual(logging.ERROR, opsdroid.get_logging_level("error"))
        self.assertEqual(logging.CRITICAL, opsdroid.get_logging_level("critical"))
        self.assertEqual(logging.INFO, opsdroid.get_logging_level(""))

    def test_configure_no_logging(self):
        config = {"logging": {"path": False, "console": False}}
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        self.assertEqual(len(rootlogger.handlers), 1)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))
        self.assertEqual(rootlogger.handlers[0].level, logging.CRITICAL)

    def test_configure_file_logging(self):
        config = {
            "logging": {
                "path": os.path.join(self._tmp_dir, "output.log"),
                "console": False,
            }
        }
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        self.assertEqual(len(rootlogger.handlers), 2)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))
        self.assertEqual(rootlogger.handlers[0].level, logging.CRITICAL)
        self.assertEqual(logging.FileHandler, type(rootlogger.handlers[1]))
        self.assertEqual(rootlogger.handlers[1].level, logging.INFO)

    def test_configure_file_blacklist(self):
        config = {
            "logging": {
                "path": os.path.join(self._tmp_dir, "output.log"),
                "console": False,
                "filter": {"blacklist": "opsdroid.logging"},
            }
        }
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        self.assertEqual(len(rootlogger.handlers), 2)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))
        self.assertEqual(rootlogger.handlers[0].level, logging.CRITICAL)
        self.assertEqual(logging.FileHandler, type(rootlogger.handlers[1]))
        self.assertEqual(rootlogger.handlers[1].level, logging.INFO)
        self.assertLogs("_LOGGER", None)

    def test_configure_file_logging_directory_not_exists(self):
        with mock.patch("logging.getLogger") as logmock:
            mocklogger = mock.MagicMock()
            mocklogger.handlers = [True]
            logmock.return_value = mocklogger
            config = {
                "logging": {
                    "path": os.path.join(
                        self._tmp_dir, "mynonexistingdirectory", "output.log"
                    ),
                    "console": False,
                }
            }
            opsdroid.configure_logging(config)

    def test_configure_console_logging(self):
        config = {"logging": {"path": False, "level": "error", "console": True}}
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        self.assertEqual(len(rootlogger.handlers), 1)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))
        self.assertEqual(rootlogger.handlers[0].level, logging.ERROR)

    def test_configure_console_blacklist(self):
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
        self.assertEqual(len(rootlogger.handlers), 1)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))
        self.assertLogs("_LOGGER", None)

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
        self.assertEqual(len(rootlogger.handlers), 1)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))
        self.assertLogs("_LOGGER", "info")

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
        self.assertEqual(len(rootlogger.handlers), 1)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))

    def test_configure_default_logging(self):
        config = {}
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        print(rootlogger)
        print(config)
        self.assertEqual(len(rootlogger.handlers), 2)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))
        self.assertEqual(rootlogger.handlers[0].level, logging.INFO)
        self.assertEqual(logging.FileHandler, type(rootlogger.handlers[1]))
        self.assertEqual(rootlogger.handlers[1].level, logging.INFO)
        self.assertLogs("_LOGGER", "info")


class TestWhiteAndBlackFilter(unittest.TestCase):
    def setUp(self):
        self.config = {
            "logging": {
                "path": False,
                "level": "info",
                "console": True,
                "filter": {"whitelist": ["opsdroid"], "blacklist": ["opsdroid.core"]},
            }
        }

    def tearDown(self):
        self.config = {}
        opsdroid.configure_logging(self.config)

    def test_configure_whitelist_and_blacklist(self):
        opsdroid.configure_logging(self.config)
        self.assertLogs("_LOGGER", "warning")

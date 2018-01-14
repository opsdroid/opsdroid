
import unittest
import logging
import os
import sys
import shutil
import tempfile
import unittest.mock as mock


import opsdroid.__main__ as opsdroid
import opsdroid.web as web
from opsdroid.core import OpsDroid
from opsdroid.helper import del_rw


class TestMain(unittest.TestCase):
    """Test the main opsdroid module."""

    def setUp(self):
        self._tmp_dir = os.path.join(tempfile.gettempdir(), "opsdroid_tests")
        try:
            os.makedirs(self._tmp_dir, mode=0o777)
        except FileExistsError:
            pass

    def tearDown(self):
        shutil.rmtree(self._tmp_dir, onerror=del_rw)

    def test_init_runs(self):
        with mock.patch.object(opsdroid, "main") as mainfunc:
            with mock.patch.object(opsdroid, "__name__", "__main__"):
                opsdroid.init()
                self.assertTrue(mainfunc.called)

    def test_init_doesnt_run(self):
        with mock.patch.object(opsdroid, "main") as mainfunc:
            with mock.patch.object(opsdroid, "__name__", "opsdroid"):
                opsdroid.init()
                self.assertFalse(mainfunc.called)

    def test_parse_args(self):
        args = opsdroid.parse_args(["--gen-config"])
        self.assertEqual(True, args.gen_config)

    def test_set_logging_level(self):
        self.assertEqual(logging.DEBUG,
                         opsdroid.get_logging_level('debug'))
        self.assertEqual(logging.INFO,
                         opsdroid.get_logging_level('info'))
        self.assertEqual(logging.WARNING,
                         opsdroid.get_logging_level('warning'))
        self.assertEqual(logging.ERROR,
                         opsdroid.get_logging_level('error'))
        self.assertEqual(logging.CRITICAL,
                         opsdroid.get_logging_level('critical'))
        self.assertEqual(logging.INFO,
                         opsdroid.get_logging_level(''))

    def test_configure_no_logging(self):
        config = {"logging": {
                    "path": False,
                    "console": False,
        }}
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        self.assertEqual(len(rootlogger.handlers), 1)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))
        self.assertEqual(rootlogger.handlers[0].level, logging.CRITICAL)

    def test_configure_file_logging(self):
        config = {"logging": {
            "path": os.path.join(self._tmp_dir, "output.log"),
            "console": False,
        }}
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        self.assertEqual(len(rootlogger.handlers), 2)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))
        self.assertEqual(rootlogger.handlers[0].level, logging.CRITICAL)
        self.assertEqual(logging.FileHandler, type(rootlogger.handlers[1]))
        self.assertEqual(rootlogger.handlers[1].level, logging.INFO)

    def test_configure_file_logging_directory_not_exists(self):
        config = {"logging": {
            "path": os.path.join(self._tmp_dir, 'mynonexistingdirectory', "output.log"),
            "console": False,
        }}
        opsdroid.configure_logging(config)
        self.assertEqual(os.path.isfile(config['logging']['path']), True)

    def test_configure_console_logging(self):
        config = {"logging": {
            "path": False,
            "level": "error",
            "console": True,
        }}
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        self.assertEqual(len(rootlogger.handlers), 1)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))
        self.assertEqual(rootlogger.handlers[0].level, logging.ERROR)

    def test_configure_default_logging(self):
        config = {}
        opsdroid.configure_logging(config)
        rootlogger = logging.getLogger()
        self.assertEqual(len(rootlogger.handlers), 2)
        self.assertEqual(logging.StreamHandler, type(rootlogger.handlers[0]))
        self.assertEqual(rootlogger.handlers[0].level, logging.INFO)
        self.assertEqual(logging.FileHandler, type(rootlogger.handlers[1]))
        self.assertEqual(rootlogger.handlers[1].level, logging.INFO)

    def test_welcome_message(self):
        config = {"welcome-message": True}
        with mock.patch('opsdroid.__main__._LOGGER.info') as logmock:
            opsdroid.welcome_message(config)
            self.assertTrue(logmock.called)

    def test_welcome_exception(self):
        config = {}
        response = opsdroid.welcome_message(config)
        self.assertIsNone(response)

    def test_check_version_27(self):
        with mock.patch.object(sys, 'version_info') as version_info:
            version_info.major = 2
            version_info.minor = 7
            with self.assertRaises(SystemExit):
                opsdroid.check_dependencies()

    def test_check_version_34(self):
        with mock.patch.object(sys, 'version_info') as version_info:
            version_info.major = 3
            version_info.minor = 4
            with self.assertRaises(SystemExit):
                opsdroid.check_dependencies()

    def test_check_version_35(self):
        with mock.patch.object(sys, 'version_info') as version_info:
            version_info.major = 3
            version_info.minor = 5
            try:
                opsdroid.check_dependencies()
            except SystemExit:
                self.fail("check_dependencies() exited unexpectedly!")

    def test_gen_config(self):
        with mock.patch.object(sys, 'argv', ["opsdroid", "--gen-config"]):
            with self.assertRaises(SystemExit):
                opsdroid.main()

    def test_main(self):
        with mock.patch.object(sys, 'argv', ["opsdroid"]), \
                mock.patch.object(opsdroid, 'check_dependencies') as mock_cd, \
                mock.patch.object(opsdroid, 'configure_logging') as mock_cl, \
                mock.patch.object(opsdroid, 'welcome_message') as mock_wm, \
                mock.patch.object(OpsDroid, 'load') as mock_load, \
                mock.patch.object(web, 'Web'), \
                mock.patch.object(OpsDroid, 'start_loop') as mock_loop:
            opsdroid.main()
            self.assertTrue(mock_cd.called)
            self.assertTrue(mock_cl.called)
            self.assertTrue(mock_wm.called)
            self.assertTrue(mock_load.called)
            self.assertTrue(mock_loop.called)

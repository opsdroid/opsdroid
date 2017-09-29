
import unittest
import logging
import os
import shutil
import mock

import opsdroid.__main__ as opsdroid


class TestMain(unittest.TestCase):
    """Test the main opsdroid module."""

    def setUp(self):
        self._tmp_dir = "/tmp/opsdroid_tests"
        os.makedirs(self._tmp_dir)

    def tearDown(self):
        shutil.rmtree(self._tmp_dir)

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
            "path": self._tmp_dir + "/output.log",
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
            "path": '/tmp/mynonexistingdirectory' + "/output.log",
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

    # def test_gen_config(self):
    #     with mock.patch.object(sys, 'argv', ["--gen-config"]):
    #         with self.assertRaises(SystemExit) as sysexit:
    #             opsdroid.main()
    #         self.assertEqual(sysexit.exception.code, 0)

    # def test_check_version(self):
    #     with mock.patch.object(sys, 'version_info', [2, 2, 0]):
    #         self.assertEqual(sys.version_info[0], 2)
    #         with self.assertRaises(SystemExit) as sysexit:
    #             opsdroid.check_dependencies()
    #         self.assertEqual(sysexit.exception.code, 1)

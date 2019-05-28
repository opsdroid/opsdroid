import unittest
import unittest.mock as mock
import os
import sys
import shutil
import tempfile
import gettext
import contextlib

import click
from click.testing import CliRunner

import opsdroid.__main__ as opsdroid
from opsdroid.__main__ import configure_lang
import opsdroid.web as web
from opsdroid.const import __version__
from opsdroid.core import OpsDroid
from opsdroid.helper import del_rw


class TestMain(unittest.TestCase):
    """Test the main opsdroid module."""

    def setUp(self):
        self._tmp_dir = os.path.join(tempfile.gettempdir(), "opsdroid_tests")
        with contextlib.suppress(FileExistsError):
            os.makedirs(self._tmp_dir, mode=0o777)
        configure_lang({})

    def tearDown(self):
        with contextlib.suppress(PermissionError):
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

    def test_configure_no_lang(self):
        with mock.patch.object(gettext, "translation") as translation:
            opsdroid.configure_lang({})
            self.assertFalse(translation.return_value.install.called)

    def test_configure_lang(self):
        with mock.patch.object(gettext, "translation") as translation:
            opsdroid.configure_lang({"lang": "es"})
            self.assertTrue(translation.return_value.install.called)

    def test_welcome_message(self):
        config = {"welcome-message": True}
        opsdroid.welcome_message(config)
        self.assertLogs("_LOGGER", "info")

    def test_welcome_exception(self):
        config = {}
        response = opsdroid.welcome_message(config)
        self.assertIsNone(response)

    def test_check_version_27(self):
        with mock.patch.object(sys, "version_info") as version_info:
            version_info.major = 2
            version_info.minor = 7
            with self.assertRaises(SystemExit):
                opsdroid.check_dependencies()

    def test_check_version_34(self):
        with mock.patch.object(sys, "version_info") as version_info:
            version_info.major = 3
            version_info.minor = 4
            with self.assertRaises(SystemExit):
                opsdroid.check_dependencies()

    def test_check_version_35(self):
        with mock.patch.object(sys, "version_info") as version_info:
            version_info.major = 3
            version_info.minor = 5
            with self.assertRaises(SystemExit):
                opsdroid.check_dependencies()

    def test_check_version_36(self):
        with mock.patch.object(sys, "version_info") as version_info:
            version_info.major = 3
            version_info.minor = 6
            try:
                opsdroid.check_dependencies()
            except SystemExit:
                self.fail("check_dependencies() exited unexpectedly!")

    def test_check_version_37(self):
        with mock.patch.object(sys, "version_info") as version_info:
            version_info.major = 3
            version_info.minor = 7
            try:
                opsdroid.check_dependencies()
            except SystemExit:
                self.fail("check_dependencies() exited unexpectedly!")

    def test_gen_config(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "opsdroid.core.OpsDroid.load"
        ) as opsdroid_load:
            runner = CliRunner()
            result = runner.invoke(opsdroid.main, ["--gen-config"])
            self.assertTrue(click_echo.called)
            self.assertFalse(opsdroid_load.called)
            self.assertEqual(result.exit_code, 0)

    def test_print_version(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "opsdroid.core.OpsDroid.load"
        ) as opsdroid_load:
            runner = CliRunner()
            result = runner.invoke(opsdroid.main, ["--version"])
            self.assertTrue(click_echo.called)
            self.assertFalse(opsdroid_load.called)
            self.assertTrue(__version__ in click_echo.call_args[0][0])
            self.assertEqual(result.exit_code, 0)

    def test_edit_files_config(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "subprocess.run"
        ) as editor:
            runner = CliRunner()
            result = runner.invoke(opsdroid.main, ["--edit-config"], input="y")
            self.assertTrue(click_echo.called)
            self.assertTrue(editor.called)
            self.assertEqual(result.exit_code, 0)

    def test_edit_files_log(self):
        with mock.patch.object(click, "echo") as click_echo, mock.patch(
            "subprocess.run"
        ) as editor:
            runner = CliRunner()
            result = runner.invoke(opsdroid.main, ["--view-log"])
            self.assertTrue(click_echo.called)
            self.assertTrue(editor.called)
            self.assertEqual(result.exit_code, 0)

    def test_main(self):
        with mock.patch.object(sys, "argv", ["opsdroid"]), mock.patch.object(
            opsdroid, "check_dependencies"
        ) as mock_cd, mock.patch.object(
            opsdroid, "configure_logging"
        ) as mock_cl, mock.patch.object(
            opsdroid, "welcome_message"
        ) as mock_wm, mock.patch.object(
            OpsDroid, "load"
        ) as mock_load, mock.patch.object(
            web, "Web"
        ), mock.patch.object(
            OpsDroid, "run"
        ) as mock_loop:
            runner = CliRunner()
            runner.invoke(opsdroid.main, [])
            self.assertTrue(mock_cd.called)
            self.assertTrue(mock_cl.called)
            self.assertTrue(mock_wm.called)
            self.assertTrue(mock_load.called)
            self.assertTrue(mock_loop.called)

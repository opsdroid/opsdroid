
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock
import importlib

from opsdroid.core import OpsDroid
from opsdroid.message import Message
from opsdroid.connector import Connector


class TestCore(unittest.TestCase):
    """Test the opsdroid core class."""

    def test_core(self):
        with OpsDroid() as opsdroid:
            self.assertIsInstance(opsdroid, OpsDroid)

    def test_exit(self):
        with OpsDroid() as opsdroid, self.assertRaises(SystemExit):
            opsdroid.eventloop = mock.Mock()
            opsdroid.eventloop.is_running.return_value = True
            opsdroid.exit()
            self.assertTrue(opsdroid.eventloop.stop.called)

    def test_critical(self):
        with OpsDroid() as opsdroid, self.assertRaises(SystemExit):
            opsdroid.critical("An error", 1)

    def test_load_config(self):
        with OpsDroid() as opsdroid:
            opsdroid.loader = mock.Mock()
            opsdroid.load()
            self.assertTrue(opsdroid.loader.load_config_file.called)

    def test_start_loop(self):
        with OpsDroid() as opsdroid:
            mockconfig = {}, {}, {}
            opsdroid.loader = mock.Mock()
            opsdroid.loader.load_config = mock.Mock(return_value=mockconfig)
            opsdroid.start_databases = mock.Mock()
            opsdroid.setup_skills = mock.Mock()
            opsdroid.start_connector_tasks = mock.Mock()
            opsdroid.eventloop.run_forever = mock.Mock()

            opsdroid.start_loop()

            self.assertTrue(opsdroid.start_databases.called)
            self.assertTrue(opsdroid.setup_skills.called)
            self.assertTrue(opsdroid.start_connector_tasks.called)
            self.assertTrue(opsdroid.eventloop.run_forever.called)

    def test_load_regex_skill(self):
        with OpsDroid() as opsdroid:
            regex = r".*"
            skill = mock.MagicMock()
            opsdroid.load_regex_skill(regex, skill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["regex"], regex)
            self.assertIsInstance(opsdroid.skills[0]["skill"], mock.MagicMock)

    def test_start_databases(self):
        with OpsDroid() as opsdroid:
            opsdroid.start_databases([])
            module = {}
            module["config"] = {}
            module["module"] = importlib.import_module(
                "tests.mockmodules.databases.database")
            with self.assertRaises(NotImplementedError):
                opsdroid.start_databases([module])
                self.assertEqual(1, len(opsdroid.memory.databases))

    def test_start_connectors(self):
        with OpsDroid() as opsdroid:
            opsdroid.start_connector_tasks([])
            module = {}
            module["config"] = {}
            module["module"] = importlib.import_module(
                "tests.mockmodules.connectors.connector")

            with self.assertRaises(NotImplementedError):
                opsdroid.start_connector_tasks([module])
                self.assertEqual(1, len(opsdroid.connectors))

            with self.assertRaises(NotImplementedError):
                opsdroid.start_connector_tasks([module, module])
                self.assertEqual(3, len(opsdroid.connectors))

    def test_multiple_opsdroids(self):
        with OpsDroid() as opsdroid:
            opsdroid.__class__.critical = mock.MagicMock()
            with OpsDroid() as opsdroid2, self.assertRaises(SystemExit):
                opsdroid2.exit()
            self.assertEqual(len(opsdroid.__class__.critical.mock_calls), 1)

    def test_setup_modules(self):
        with OpsDroid() as opsdroid:
            example_modules = []
            example_modules.append({"module": mock.MagicMock()})
            example_modules.append({"module": {"name": "test"}})
            opsdroid.setup_skills(example_modules)
            self.assertEqual(len(example_modules[0]["module"].mock_calls), 1)


class TestCoreAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid core class."""

    async def test_parse(self):
        with OpsDroid() as opsdroid:
            regex = r".*"
            skill = amock.CoroutineMock()
            mock_connector = Connector({})
            opsdroid.load_regex_skill(regex, skill)
            message = Message("Hello world", "user", "default", mock_connector)
            await opsdroid.parse(message)
            self.assertTrue(skill.called)

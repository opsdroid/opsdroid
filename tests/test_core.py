
import asyncio
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock
import importlib

from opsdroid.core import OpsDroid
from opsdroid.message import Message
from opsdroid.connector import Connector
from opsdroid.matchers import (match_regex, match_dialogflow_action,
                               match_luisai_intent, match_recastai,
                               match_witai)


class TestCore(unittest.TestCase):
    """Test the opsdroid core class."""

    def setUp(self):
        self.previous_loop = asyncio.get_event_loop()

    def tearDown(self):
        self.previous_loop.close()
        asyncio.set_event_loop(asyncio.new_event_loop())

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

    def test_stop(self):
        with OpsDroid() as opsdroid:
            self.assertFalse(opsdroid.eventloop.is_closed())
            opsdroid.stop()
            self.assertFalse(opsdroid.eventloop.is_running())

    def test_call_stop(self):
        with OpsDroid() as opsdroid:
            opsdroid.stop = mock.Mock()
            opsdroid.disconnect = amock.CoroutineMock()

            opsdroid.call_stop()

            self.assertTrue(opsdroid.disconnect.called)

    def test_restart(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop.create_task(asyncio.sleep(1))
            self.assertFalse(opsdroid.should_restart)
            opsdroid.restart()
            self.assertTrue(opsdroid.should_restart)

    def test_load_config(self):
        with OpsDroid() as opsdroid:
            opsdroid.loader = mock.Mock()
            opsdroid.load()
            self.assertTrue(opsdroid.loader.load_config_file.called)

    @asynctest.patch('opsdroid.core.parse_crontab')
    def test_start_loop(self, mocked_parse_crontab):
        with OpsDroid() as opsdroid:
            mockconfig = {}, {}, {}
            opsdroid.web_server = mock.Mock()
            opsdroid.loader = mock.Mock()
            opsdroid.loader.load_modules_from_config = \
                mock.Mock(return_value=mockconfig)
            opsdroid.start_databases = mock.Mock()
            opsdroid.setup_skills = mock.Mock()
            opsdroid.start_connector_tasks = mock.Mock()
            opsdroid.eventloop.run_forever = mock.Mock()

            with self.assertRaises(RuntimeError):
                opsdroid.start_loop()

            self.assertTrue(opsdroid.start_databases.called)
            self.assertTrue(opsdroid.setup_skills.called)
            self.assertTrue(opsdroid.start_connector_tasks.called)
            self.assertTrue(opsdroid.eventloop.run_forever.called)

    def test_load_regex_skill(self):
        with OpsDroid() as opsdroid:
            regex = r".*"
            skill = mock.MagicMock()
            decorator = match_regex(regex)
            decorator(skill)
            self.assertEqual(len(opsdroid.skills), 1)
            self.assertEqual(opsdroid.skills[0]["regex"]["expression"], regex)
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

    def test_default_connector(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector({})
            opsdroid.connectors.append(mock_connector)
            self.assertEqual(opsdroid.default_connector, mock_connector)

            mock_default_connector = Connector({"default": True})
            opsdroid.connectors.append(mock_default_connector)
            self.assertEqual(opsdroid.default_connector,
                             mock_default_connector)

    def test_default_room(self):
        mock_connector = Connector({})
        self.assertEqual(None, mock_connector.default_room)


class TestCoreAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid core class."""

    async def test_disconnect(self):
        with OpsDroid() as opsdroid:
            connector = Connector({})
            opsdroid.connectors.append(connector)
            connector.disconnect = amock.CoroutineMock()

            await opsdroid.disconnect()

            self.assertTrue(connector.disconnect.called)

    async def test_parse_regex(self):
        with OpsDroid() as opsdroid:
            regex = r"Hello .*"
            skill = amock.CoroutineMock()
            mock_connector = Connector({})
            match_regex(regex)(skill)
            message = Message("Hello world", "user", "default", mock_connector)
            tasks = await opsdroid.parse(message)
            for task in tasks:
                await task
            self.assertTrue(skill.called)

    async def test_parse_regex_insensitive(self):
        with OpsDroid() as opsdroid:
            regex = r"Hello .*"
            skill = amock.CoroutineMock()
            mock_connector = Connector({})
            match_regex(regex, case_sensitive=False)(skill)
            message = Message("HELLO world", "user", "default", mock_connector)
            tasks = await opsdroid.parse(message)
            for task in tasks:
                await task
            self.assertTrue(skill.called)

    async def test_parse_dialogflow(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "dialogflow"}]
            dialogflow_action = ""
            skill = amock.CoroutineMock()
            mock_connector = Connector({})
            match_dialogflow_action(dialogflow_action)(skill)
            message = Message("Hello world", "user", "default", mock_connector)
            with amock.patch('opsdroid.parsers.dialogflow.parse_dialogflow'):
                tasks = await opsdroid.parse(message)
                self.assertEqual(len(tasks), 1)

                # Once apiai parser stops working, remove this test!
                with amock.patch('opsdroid.core._LOGGER.warning') as logmock:
                    opsdroid.config["parsers"] = [{"name": "apiai"}]
                    tasks = await opsdroid.parse(message)
                    self.assertTrue(logmock.called)

                # But leave this bit
                for task in tasks:
                    await task

    async def test_parse_luisai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "luisai"}]
            luisai_intent = ""
            skill = amock.CoroutineMock()
            mock_connector = Connector({})
            match_luisai_intent(luisai_intent)(skill)
            message = Message("Hello world", "user", "default", mock_connector)
            with amock.patch('opsdroid.parsers.luisai.parse_luisai'):
                tasks = await opsdroid.parse(message)
                self.assertEqual(len(tasks), 1)
                for task in tasks:
                    await task

    async def test_parse_recastai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "recastai"}]
            recastai_intent = ""
            skill = amock.CoroutineMock()
            mock_connector = Connector({})
            match_recastai(recastai_intent)(skill)
            message = Message("Hello", "user", "default", mock_connector)
            with amock.patch('opsdroid.parsers.recastai.parse_recastai'):
                tasks = await opsdroid.parse(message)
                self.assertEqual(len(tasks), 1)
                for task in tasks:
                    await task

    async def test_parse_witai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "witai"}]
            witai_intent = ""
            skill = amock.CoroutineMock()
            mock_connector = Connector({})
            match_witai(witai_intent)(skill)
            message = Message("Hello world", "user", "default", mock_connector)
            with amock.patch('opsdroid.parsers.witai.parse_witai'):
                tasks = await opsdroid.parse(message)
                self.assertEqual(len(tasks), 1)
                for task in tasks:
                    await task

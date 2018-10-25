
import asyncio
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock
import importlib

from opsdroid.__main__ import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.message import Message
from opsdroid.connector import Connector
from opsdroid.matchers import (match_regex, match_dialogflow_action,
                               match_luisai_intent, match_recastai,
                               match_rasanlu, match_witai)


class TestCore(unittest.TestCase):
    """Test the opsdroid core class."""

    def setUp(self):
        self.previous_loop = asyncio.get_event_loop()
        configure_lang({})

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
            opsdroid.eventloop.create_task(asyncio.sleep(0))
            self.assertFalse(opsdroid.eventloop.is_closed())
            opsdroid.stop()
            self.assertFalse(opsdroid.eventloop.is_running())

    def test_call_stop(self):
        with OpsDroid() as opsdroid:
            opsdroid.stop = mock.Mock()
            opsdroid.disconnect = amock.CoroutineMock()

            opsdroid.call_stop()

            self.assertTrue(opsdroid.disconnect.called)

    def test_load_config(self):
        with OpsDroid() as opsdroid:
            opsdroid.loader.load_modules_from_config = mock.Mock()
            opsdroid.loader.load_modules_from_config.return_value = \
                {"skills": [], "databases": [], "connectors": []}
            opsdroid.load({})
            self.assertTrue(opsdroid.loader.load_modules_from_config.called)

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
            opsdroid.modules = {"skills": [],
                                "databases": [],
                                "connectors": []}

            with self.assertRaises(RuntimeError):
                opsdroid.start_loop()

            self.assertTrue(opsdroid.start_databases.called)
            self.assertTrue(opsdroid.start_connector_tasks.called)
            self.assertTrue(opsdroid.eventloop.run_forever.called)

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
                "tests.mockmodules.connectors.connector_mocked")

            try:
                opsdroid.start_connector_tasks([module])
            except NotImplementedError:
                self.fail("Connector raised NotImplementedError.")

    def test_start_connectors_not_implemented(self):
        with OpsDroid() as opsdroid:
            opsdroid.start_connector_tasks([])

            module = {}
            module["config"] = {}
            module["module"] = importlib.import_module(
                "tests.mockmodules.connectors.connector_bare")

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
            mockskill = lambda x: x * 2
            mockskill.skill = True
            mockmodule = mock.Mock(setup=mock.MagicMock(), mockskill=mockskill)
            example_modules.append({"module": mockmodule, "config": {}})
            opsdroid.setup_skills(example_modules)
            self.assertEqual(len(mockmodule.setup.mock_calls), 1)
            self.assertEqual(mockmodule.method_calls[0][0], 'setup')
            self.assertEqual(len(mockmodule.method_calls[0][1]), 2)
            self.assertEqual(mockmodule.method_calls[0][1][1], {})

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

    def test_train_rasanlu(self):
        with OpsDroid() as opsdroid:
            opsdroid.eventloop = asyncio.new_event_loop()
            opsdroid.config["parsers"] = [{"name": "rasanlu"}]
            with amock.patch('opsdroid.parsers.rasanlu.train_rasanlu'):
                opsdroid.train_parsers({})
                opsdroid.eventloop.close()


class TestCoreAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid core class."""

    async def setUp(self):
        configure_lang({})

    async def getMockSkill(self):
        async def mockedskill(opsdroid, config, message):
            await message.respond("Test")
        mockedskill.config = {}
        return mockedskill

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
            mock_connector = Connector({})
            mock_connector.respond = amock.CoroutineMock()
            skill = await self.getMockSkill()
            opsdroid.skills.append(match_regex(regex)(skill))
            message = Message("Hello world", "user", "default", mock_connector)
            tasks = await opsdroid.parse(message)
            for task in tasks:
                await task
            self.assertTrue(mock_connector.respond.called)

    async def test_parse_regex_insensitive(self):
        with OpsDroid() as opsdroid:
            regex = r"Hello .*"
            mock_connector = Connector({})
            mock_connector.respond = amock.CoroutineMock()
            skill = await self.getMockSkill()
            opsdroid.skills.append(match_regex(regex, case_sensitive=False)(skill))
            message = Message("HELLO world", "user", "default", mock_connector)
            tasks = await opsdroid.parse(message)
            for task in tasks:
                await task
            self.assertTrue(mock_connector.respond.called)

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

    async def test_parse_rasanlu(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = [{"name": "rasanlu"}]
            rasanlu_intent = ""
            skill = amock.CoroutineMock()
            mock_connector = Connector({})
            match_rasanlu(rasanlu_intent)(skill)
            message = Message("Hello", "user", "default", mock_connector)
            with amock.patch('opsdroid.parsers.rasanlu.parse_rasanlu'):
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

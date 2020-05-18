import os
import asyncio
import contextlib
import unittest
import unittest.mock as mock
import asynctest
import asynctest.mock as amock
import importlib

from opsdroid.cli.start import configure_lang
from opsdroid.core import OpsDroid
from opsdroid.events import Message
from opsdroid.connector import Connector
from opsdroid.database import Database
from opsdroid.web import Web
from opsdroid.matchers import (
    match_regex,
    match_dialogflow_action,
    match_luisai_intent,
    match_sapcai,
    match_rasanlu,
    match_watson,
    match_witai,
)


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

    def test_is_running(self):
        with OpsDroid() as opsdroid:
            self.assertFalse(opsdroid.is_running())
            opsdroid._running = True
            self.assertTrue(opsdroid.is_running())

    def test_critical(self):
        with OpsDroid() as opsdroid, self.assertRaises(SystemExit):
            opsdroid.critical("An error", 1)

    def test_load_modules(self):
        with OpsDroid() as opsdroid:
            opsdroid.loader.load_modules_from_config = mock.Mock()
            opsdroid.loader.load_modules_from_config.return_value = {
                "skills": [],
                "databases": [],
                "connectors": [],
            }
            with self.assertRaises(SystemExit):
                opsdroid.eventloop.run_until_complete(opsdroid.load())
            self.assertTrue(opsdroid.loader.load_modules_from_config.called)

    def test_run(self):
        with OpsDroid() as opsdroid:
            opsdroid.is_running = amock.Mock(side_effect=[False, True, False])
            opsdroid.eventloop = mock.MagicMock()
            opsdroid.eventloop.run_until_complete = mock.Mock()

            with mock.patch("sys.exit") as mock_sysexit:
                opsdroid.run()

            self.assertTrue(opsdroid.eventloop.run_until_complete.called)
            self.assertTrue(mock_sysexit.called)

    def test_run_cancelled(self):
        with OpsDroid() as opsdroid:
            opsdroid.is_running = amock.Mock(side_effect=[False, True, False])
            opsdroid.eventloop = mock.MagicMock()
            opsdroid.eventloop.run_until_complete = mock.Mock(
                side_effect=asyncio.CancelledError
            )
            opsdroid.sync_load = mock.MagicMock()

            with mock.patch("sys.exit") as mock_sysexit:
                opsdroid.run()

            self.assertTrue(opsdroid.eventloop.run_until_complete.called)
            self.assertTrue(mock_sysexit.called)

    def test_run_already_running(self):
        with OpsDroid() as opsdroid:
            opsdroid._running = True
            opsdroid.eventloop = mock.MagicMock()
            opsdroid.eventloop.run_until_complete = mock.Mock(
                side_effect=asyncio.CancelledError
            )
            opsdroid.sync_load = mock.MagicMock()

            with mock.patch("sys.exit") as mock_sysexit:
                opsdroid.run()

            self.assertFalse(opsdroid.eventloop.run_until_complete.called)
            self.assertFalse(mock_sysexit.called)

    @asynctest.patch("opsdroid.core.parse_crontab")
    def test_load(self, mocked_parse_crontab):
        with OpsDroid() as opsdroid:
            mockconfig = {
                "skills": [],
                "databases": [{"name": "mockdb"}],
                "connectors": [],
            }
            opsdroid.web_server = mock.Mock()
            opsdroid.loader = mock.Mock()
            opsdroid.loader.load_modules_from_config = mock.Mock(
                return_value=mockconfig
            )
            opsdroid.start_databases = amock.CoroutineMock()
            opsdroid.setup_skills = mock.Mock()
            opsdroid.start_connectors = amock.CoroutineMock()

            opsdroid.eventloop.run_until_complete(opsdroid.load())

            self.assertTrue(opsdroid.start_databases.called)
            self.assertTrue(opsdroid.start_connectors.called)

    def test_multiple_opsdroids(self):
        with OpsDroid() as opsdroid:
            opsdroid.__class__.critical = mock.MagicMock()
            with OpsDroid() as opsdroid2, self.assertRaises(SystemExit):
                opsdroid2.exit()
            self.assertEqual(len(opsdroid.__class__.critical.mock_calls), 1)

    def test_setup_modules(self):
        with OpsDroid() as opsdroid:

            def mockskill(x):
                return x * 2

            mockskill.skill = True
            mockmodule = mock.Mock(setup=mock.MagicMock(), mockskill=mockskill)
            example_modules = [{"module": mockmodule, "config": {}}]
            opsdroid.setup_skills(example_modules)
            self.assertEqual(len(mockmodule.setup.mock_calls), 1)
            self.assertEqual(mockmodule.method_calls[0][0], "setup")
            self.assertEqual(len(mockmodule.method_calls[0][1]), 2)
            self.assertEqual(mockmodule.method_calls[0][1][1], {})
            self.assertEqual(len(opsdroid.skills), 2)

            mockclassmodule = importlib.import_module(
                "tests.mockmodules.skills.skill.skilltest"
            )
            example_modules = [{"module": mockclassmodule, "config": {}}]
            opsdroid.setup_skills(example_modules)
            self.assertEqual(len(opsdroid.skills), 3)

    def test_default_connector(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector({}, opsdroid=opsdroid)
            opsdroid.connectors.append(mock_connector)
            self.assertEqual(opsdroid.default_connector, mock_connector)

            mock_default_connector = Connector({"default": True}, opsdroid=opsdroid)
            opsdroid.connectors.append(mock_default_connector)
            self.assertEqual(opsdroid.default_connector, mock_default_connector)

    def test_default_target(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector({}, opsdroid=opsdroid)
            self.assertEqual(None, mock_connector.default_target)

    def test_connector_names(self):
        with OpsDroid() as opsdroid:
            with self.assertRaises(ValueError):
                opsdroid._connector_names

            # Ensure names are always unique
            c1 = Connector({"name": "spam"}, opsdroid=opsdroid)
            c2 = Connector({"name": "spam"}, opsdroid=opsdroid)

            opsdroid.connectors = [c1, c2]

            names = opsdroid._connector_names
            assert "spam" in names
            assert "spam_1" in names


class TestCoreAsync(asynctest.TestCase):
    """Test the async methods of the opsdroid core class."""

    async def setUp(self):
        configure_lang({})

    async def getMockSkill(self):
        async def mockedskill(opsdroid, config, message):
            await message.respond("Test")

        mockedskill.config = {}
        return mockedskill

    async def getMockMethodSkill(self):
        async def mockedskill(message):
            await message.respond("Test")

        mockedskill.config = {}
        return mockedskill

    async def test_handle_signal(self):
        with OpsDroid() as opsdroid:
            opsdroid._running = True
            self.assertTrue(opsdroid.is_running())
            opsdroid.unload = amock.CoroutineMock()
            await opsdroid.handle_signal()
            self.assertFalse(opsdroid.is_running())
            self.assertTrue(opsdroid.unload.called)

    async def test_unload(self):
        with OpsDroid() as opsdroid:
            mock_connector = Connector({}, opsdroid=opsdroid)
            mock_connector.disconnect = amock.CoroutineMock()
            opsdroid.connectors = [mock_connector]

            mock_database = Database({})
            mock_database.disconnect = amock.CoroutineMock()
            opsdroid.memory.databases = [mock_database]

            mock_skill = amock.Mock(config={"name": "mockskill"})
            opsdroid.skills = [mock_skill]

            opsdroid.web_server = Web(opsdroid)
            opsdroid.web_server.stop = amock.CoroutineMock()
            mock_web_server = opsdroid.web_server

            opsdroid.cron_task = amock.CoroutineMock()
            opsdroid.cron_task.cancel = amock.CoroutineMock()
            mock_cron_task = opsdroid.cron_task

            opsdroid.path_watch_task = amock.CoroutineMock()
            opsdroid.path_watch_task.cancel = amock.CoroutineMock()
            mock_path_watch_task = opsdroid.path_watch_task

            async def task():
                await asyncio.sleep(0.5)

            t = asyncio.Task(task(), loop=self.loop)

            await opsdroid.unload()

            self.assertTrue(t.cancel())
            self.assertTrue(mock_connector.disconnect.called)
            self.assertTrue(mock_database.disconnect.called)
            self.assertTrue(mock_web_server.stop.called)
            self.assertTrue(opsdroid.web_server is None)
            self.assertTrue(mock_cron_task.cancel.called)
            self.assertTrue(mock_path_watch_task.cancel.called)
            self.assertTrue(opsdroid.cron_task is None)
            self.assertFalse(opsdroid.connectors)
            self.assertFalse(opsdroid.memory.databases)
            self.assertFalse(opsdroid.skills)

    async def test_reload(self):
        with OpsDroid() as opsdroid:
            opsdroid.load = amock.CoroutineMock()
            opsdroid.unload = amock.CoroutineMock()
            await opsdroid.reload()
            self.assertTrue(opsdroid.load.called)
            self.assertTrue(opsdroid.unload.called)

    async def test_parse_regex(self):
        with OpsDroid() as opsdroid:
            regex = r"Hello .*"
            mock_connector = Connector({}, opsdroid=opsdroid)
            mock_connector.send = amock.CoroutineMock()
            skill = await self.getMockSkill()
            opsdroid.skills.append(match_regex(regex)(skill))
            message = Message(
                text="Hello World",
                user="user",
                target="default",
                connector=mock_connector,
            )
            await opsdroid.parse(message)
            self.assertTrue(mock_connector.send.called)

    async def test_parse_regex_method_skill(self):
        with OpsDroid() as opsdroid:
            regex = r"Hello .*"
            mock_connector = Connector({}, opsdroid=opsdroid)
            mock_connector.send = amock.CoroutineMock()
            skill = await self.getMockMethodSkill()
            opsdroid.skills.append(match_regex(regex)(skill))
            message = Message(
                text="Hello world",
                user="user",
                target="default",
                connector=mock_connector,
            )
            await opsdroid.parse(message)
            self.assertTrue(mock_connector.send.called)

    async def test_parse_regex_insensitive(self):
        with OpsDroid() as opsdroid:
            regex = r"Hello .*"
            mock_connector = Connector({}, opsdroid=opsdroid)
            mock_connector.send = amock.CoroutineMock()
            skill = await self.getMockSkill()
            opsdroid.skills.append(match_regex(regex, case_sensitive=False)(skill))
            message = Message(
                text="HELLO world",
                user="user",
                target="default",
                connector=mock_connector,
            )
            await opsdroid.parse(message)
            self.assertTrue(mock_connector.send.called)

    async def test_parse_dialogflow(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/test.json"
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = {
                "dialogflow": {"project-id": "test", "enabled": True}
            }
            dialogflow_action = "smalltalk.greetings.whatsup"
            skill = amock.CoroutineMock()
            mock_connector = Connector({}, opsdroid=opsdroid)
            match_dialogflow_action(dialogflow_action)(skill)
            message = Message(
                text="Hello world",
                user="user",
                target="default",
                connector=mock_connector,
            )
            with amock.patch(
                "opsdroid.parsers.dialogflow.parse_dialogflow"
            ), amock.patch("opsdroid.parsers.dialogflow.call_dialogflow"):
                tasks = await opsdroid.parse(message)
                self.assertEqual(len(tasks), 2)

                tasks = await opsdroid.parse(message)
                self.assertLogs("_LOGGER", "warning")

    async def test_parse_luisai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = {"luisai": {"enabled": True}}
            luisai_intent = ""
            skill = amock.CoroutineMock()
            mock_connector = Connector({}, opsdroid=opsdroid)
            match_luisai_intent(luisai_intent)(skill)
            message = Message(
                text="Hello world",
                user="user",
                target="default",
                connector=mock_connector,
            )
            with amock.patch("opsdroid.parsers.luisai.parse_luisai"):
                tasks = await opsdroid.parse(message)
                self.assertEqual(len(tasks), 2)

    async def test_parse_rasanlu(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = {"rasanlu": {"enabled": True}}
            rasanlu_intent = ""
            skill = amock.CoroutineMock()
            mock_connector = Connector({}, opsdroid=opsdroid)
            match_rasanlu(rasanlu_intent)(skill)
            message = Message(
                text="Hello", user="user", target="default", connector=mock_connector
            )
            with amock.patch("opsdroid.parsers.rasanlu.parse_rasanlu"):
                tasks = await opsdroid.parse(message)
                self.assertEqual(len(tasks), 2)

    async def test_parse_sapcai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = {"sapcai": {"enabled": True}}
            sapcai_intent = ""
            skill = amock.CoroutineMock()
            mock_connector = Connector({}, opsdroid=opsdroid)
            match_sapcai(sapcai_intent)(skill)
            message = Message(
                text="Hello", user="user", target="default", connector=mock_connector
            )
            with amock.patch("opsdroid.parsers.sapcai.parse_sapcai"):
                tasks = await opsdroid.parse(message)
                self.assertEqual(len(tasks), 2)

    async def test_parse_watson(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = {"watson": {"enabled": True}}
            watson_intent = ""
            skill = amock.CoroutineMock()
            mock_connector = Connector({}, opsdroid=opsdroid)
            match_watson(watson_intent)(skill)
            message = Message("Hello world", "user", "default", mock_connector)
            with amock.patch("opsdroid.parsers.watson.parse_watson"):
                tasks = await opsdroid.parse(message)
                self.assertEqual(len(tasks), 2)

    async def test_parse_witai(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = {"witai": {"enabled": True}}
            witai_intent = ""
            skill = amock.CoroutineMock()
            mock_connector = Connector({}, opsdroid=opsdroid)
            match_witai(witai_intent)(skill)
            message = Message(
                text="Hello world",
                user="user",
                target="default",
                connector=mock_connector,
            )
            with amock.patch("opsdroid.parsers.witai.parse_witai"):
                tasks = await opsdroid.parse(message)
                self.assertEqual(len(tasks), 2)

    async def test_send_default_one(self):
        with OpsDroid() as opsdroid, amock.patch(
            "opsdroid.connector.Connector.send"
        ) as patched_send:
            connector = Connector({"name": "shell"})
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result("")

            opsdroid.connectors = [connector]

            input_message = Message("Test")
            await opsdroid.send(input_message)

            message = patched_send.call_args[0][0]

            assert message is input_message

    async def test_send_default_explicit(self):
        with OpsDroid() as opsdroid, amock.patch(
            "opsdroid.connector.Connector.send"
        ) as patched_send:
            connector = Connector({"name": "shell", "default": True})
            connector2 = Connector({"name": "matrix"})
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result("")

            opsdroid.connectors = [connector, connector2]

            input_message = Message("Test")
            await opsdroid.send(input_message)

            message = patched_send.call_args[0][0]

            assert message is input_message

    async def test_send_name(self):
        with OpsDroid() as opsdroid, amock.patch(
            "opsdroid.connector.Connector.send"
        ) as patched_send:
            connector = Connector({"name": "shell"})
            connector2 = Connector({"name": "matrix"})
            patched_send.return_value = asyncio.Future()
            patched_send.return_value.set_result("")

            opsdroid.connectors = [connector, connector2]

            input_message = Message(text="Test", connector="shell")
            await opsdroid.send(input_message)

            message = patched_send.call_args[0][0]

            assert message is input_message

    async def test_start_connectors(self):
        with OpsDroid() as opsdroid:
            await opsdroid.start_connectors([])

            module = {}
            module["config"] = {}
            module["module"] = importlib.import_module(
                "tests.mockmodules.connectors.connector_mocked"
            )

            try:
                await opsdroid.start_connectors([module])
            except NotImplementedError:
                self.fail("Connector raised NotImplementedError.")
            self.assertEqual(len(opsdroid.connectors), 1)

            with mock.patch.object(opsdroid.eventloop, "is_running", return_value=True):
                await opsdroid.start_connectors([module])
                self.assertEqual(len(opsdroid.connectors), 2)

    async def test_start_connectors_not_implemented(self):
        with OpsDroid() as opsdroid:
            await opsdroid.start_connectors([])

            module = {}
            module["config"] = {}
            module["module"] = importlib.import_module(
                "tests.mockmodules.connectors.connector_bare"
            )

            with self.assertRaises(NotImplementedError):
                await opsdroid.start_connectors([module])
                self.assertEqual(1, len(opsdroid.connectors))

            with self.assertRaises(NotImplementedError):
                await opsdroid.start_connectors([module, module])
                self.assertEqual(3, len(opsdroid.connectors))

    async def test_start_databases(self):
        with OpsDroid() as opsdroid:
            await opsdroid.start_databases([])
            module = {}
            module["config"] = {}
            module["module"] = importlib.import_module(
                "tests.mockmodules.databases.database"
            )
            with self.assertRaises(NotImplementedError):
                await opsdroid.start_databases([module])
                self.assertEqual(1, len(opsdroid.memory.databases))

    async def test_train_rasanlu(self):
        with OpsDroid() as opsdroid:
            opsdroid.config["parsers"] = {"rasanlu": {"enabled": True}}
            with amock.patch("opsdroid.parsers.rasanlu.train_rasanlu"):
                await opsdroid.train_parsers({})

    async def test_watchdog_works(self):
        from watchgod import awatch, PythonWatcher
        from tempfile import TemporaryDirectory
        import os.path
        import asyncio

        async def watch_dirs(directories):
            async def watch_dir(directory):
                async for changes in awatch(directory, watcher_cls=PythonWatcher):
                    assert changes
                    break

            await asyncio.gather(*[watch_dir(directory) for directory in directories])

        async def modify_dir(directory):
            await asyncio.sleep(0.1)
            with open(os.path.join(directory, "test.py"), "w") as fh:
                fh.write("")

        with TemporaryDirectory() as directory:
            await asyncio.gather(watch_dirs([directory]), modify_dir(directory))

    async def test_watchdog(self):
        skill_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "mockmodules/skills/skill/skilltest",
        )
        example_config = {
            "autoreload": True,
            "connectors": {"websocket": {}},
            "skills": {"test": {"path": skill_path}},
        }

        async def modify_dir(opsdroid, directory):
            await asyncio.sleep(0.1)
            mock_file_path = os.path.join(directory, "mock.py")
            with open(mock_file_path, "w") as fh:
                fh.write("")
            await asyncio.sleep(0.5)
            opsdroid.path_watch_task.cancel()
            os.remove(mock_file_path)

        with OpsDroid(config=example_config) as opsdroid:
            opsdroid.reload = amock.CoroutineMock()
            await opsdroid.load()

            with contextlib.suppress(asyncio.CancelledError):
                await asyncio.gather(
                    opsdroid.path_watch_task, modify_dir(opsdroid, skill_path)
                )

            assert opsdroid.reload.called

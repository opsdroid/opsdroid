"""Core components of OpsDroid."""

import copy
import logging
import os
import signal
import sys
import weakref
import asyncio
import contextlib
import inspect
from watchgod import awatch, PythonWatcher

from opsdroid import events
from opsdroid.const import DEFAULT_CONFIG_LOCATIONS
from opsdroid.memory import Memory
from opsdroid.connector import Connector
from opsdroid.configuration import load_config_file
from opsdroid.database import Database, InMemoryDatabase
from opsdroid.skill import Skill
from opsdroid.loader import Loader
from opsdroid.web import Web
from opsdroid.parsers.always import parse_always
from opsdroid.parsers.catchall import parse_catchall
from opsdroid.parsers.event_type import parse_event_type
from opsdroid.parsers.regex import parse_regex
from opsdroid.parsers.parseformat import parse_format
from opsdroid.parsers.dialogflow import parse_dialogflow
from opsdroid.parsers.luisai import parse_luisai
from opsdroid.parsers.sapcai import parse_sapcai
from opsdroid.parsers.witai import parse_witai
from opsdroid.parsers.watson import parse_watson
from opsdroid.parsers.rasanlu import parse_rasanlu, train_rasanlu
from opsdroid.parsers.crontab import parse_crontab
from opsdroid.helper import get_parser_config


_LOGGER = logging.getLogger(__name__)


class OpsDroid:
    """Root object for opsdroid."""

    # pylint: disable=too-many-instance-attributes
    # All are reasonable in this case.

    instances = []

    def __init__(self, config=None, config_path=None):
        """Start opsdroid."""
        self.bot_name = "opsdroid"
        self._running = False
        self.sys_status = 0
        self.connectors = []
        self.eventloop = asyncio.get_event_loop()
        if os.name != "nt":
            for sig in (signal.SIGINT, signal.SIGTERM):
                self.eventloop.add_signal_handler(
                    sig, lambda: asyncio.ensure_future(self.handle_stop_signal())
                )
            self.eventloop.add_signal_handler(
                signal.SIGHUP, lambda: asyncio.ensure_future(self.reload())
            )
        self.eventloop.set_exception_handler(self.handle_async_exception)
        self.skills = []
        self.memory = Memory()
        self.modules = {}
        self.loader = Loader(self)
        self.config_path = config_path if config_path else DEFAULT_CONFIG_LOCATIONS
        if config is None:
            self.config = {}
        else:
            self.config = config
        self.stats = {
            "messages_parsed": 0,
            "webhooks_called": 0,
            "total_response_time": 0,
            "total_responses": 0,
        }
        self.web_server = None
        self.stored_path = []
        self.reload_paths = []
        self.tasks = []

    def __enter__(self):
        """Add self to existing instances."""
        self.stored_path = copy.copy(sys.path)
        if not self.__class__.instances:
            self.__class__.instances.append(weakref.proxy(self))
        else:
            self.critical("opsdroid has already been started", 1)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Remove self from existing instances."""
        sys.path = self.stored_path
        self.__class__.instances = []
        asyncio.set_event_loop(asyncio.new_event_loop())

    @property
    def default_connector(self):
        """Return the default connector.

        Returns:
            default_connector (connector object): A connector that was configured as default.

        """
        default_connector = None
        for connector in self.connectors:
            if "default" in connector.config and connector.config["default"]:
                default_connector = connector
                break
        if default_connector is None:
            default_connector = self.connectors[0]
        return default_connector

    def exit(self):
        """Exit application."""
        _LOGGER.info(
            _("Exiting application with return code %s."), str(self.sys_status)
        )
        sys.exit(self.sys_status)

    def critical(self, error, code):
        """Exit due to unrecoverable error.

        Args:
            error (String): Describes the error encountered.
            code (Integer): Error code to exit with.

        """
        self.sys_status = code
        _LOGGER.critical(error)
        self.exit()

    @staticmethod
    def handle_async_exception(loop, context):
        """Handle exceptions from async coroutines.

        Args:
            loop (asyncio.loop): Running loop that raised the exception.
            context (String): Describes the exception encountered.

        """
        print("ERROR: Unhandled exception in opsdroid, exiting...")
        if "future" in context:
            try:  # pragma: nocover
                context["future"].result()
            # pylint: disable=broad-except
            except Exception:  # pragma: nocover
                print("Caught exception")
                print(context)

    def is_running(self):
        """Check whether opsdroid is running."""
        return self._running

    async def handle_stop_signal(self):
        """Handle signals."""
        self._running = False
        await self.stop()
        await self.unload()

    def run(self):
        """Start the event loop."""
        self.sync_load()
        if not self.is_running():
            _LOGGER.info(_("Opsdroid is now running, press ctrl+c to exit."))
            self._running = True
            while self.is_running():
                with contextlib.suppress(asyncio.CancelledError):
                    self.eventloop.run_until_complete(self.start())

            self.eventloop.stop()
            self.eventloop.close()

            _LOGGER.info(_("Bye!"))
            self.exit()
        else:
            _LOGGER.error(_("Oops! Opsdroid is already running."))

    async def start(self):
        """Create tasks and then run all created tasks concurrently."""
        if len(self.skills) == 0:
            self.critical(_("No skills in configuration, at least 1 required"), 1)

        await self.start_connectors()
        self.create_task(self.start_databases())
        self.create_task(self.watch_paths())
        self.create_task(parse_crontab(self))
        self.create_task(self.web_server.start())

        self.create_task(self.parse(events.OpsdroidStarted()))

        await self._run_tasks()

    async def _run_tasks(self):
        """
        Run all created tasks concurrently.

        This is separate from start() so that tests can run the loop without
        creating any of the tasks.
        """
        self._running = True
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*self.tasks)
        self._running = False

    def create_task(self, task):
        """Create an async task and add it to the list of tasks."""
        self.tasks.append(self.eventloop.create_task(task))

    def sync_load(self):
        """Run the load modules method synchronously."""
        self.eventloop.run_until_complete(self.load())

    async def load(self, config=None):
        """Load modules."""
        if config is not None:
            self.config = config
        self.modules = self.loader.load_modules_from_config(self.config)
        _LOGGER.debug(_("Loaded %i skills."), len(self.modules["skills"] or []))
        self.web_server = Web(self)
        self.setup_skills(self.modules["skills"])
        await self.setup_databases(self.modules["databases"])
        await self.setup_connectors(self.modules["connectors"])
        self.web_server.setup_webhooks(self.skills)
        await self.train_parsers(self.modules["skills"])

    async def stop(self):
        """Stop all tasks running in opsdroid."""
        _LOGGER.info(_("Received stop signal, exiting."))

        for connector in self.connectors:
            _LOGGER.info(_("Stopping connector %s..."), connector.name)
            await connector.disconnect()
            _LOGGER.info(_("Stopped connector %s."), connector.name)

        for database in self.memory.databases[:]:
            _LOGGER.info(_("Stopping database %s..."), database.name)
            await database.disconnect()
            _LOGGER.info(_("Stopped database %s."), database.name)

        _LOGGER.info(_("Stopping web server..."))
        await self.web_server.stop()
        _LOGGER.info(_("Stopped web server."))

        _LOGGER.info(_("Stopping pending tasks..."))
        for task in self.tasks:
            if not task.done() and task is not asyncio.current_task():
                task.cancel()
        _LOGGER.info(_("Stopped pending tasks."))

    async def unload(self, future=None):
        """Stop the event loop."""
        self.skills = []
        self.connectors = []
        self.memory.databases = []
        self.web_server = None
        self.modules = {}

    async def reload(self):
        """Reload opsdroid."""
        await self.stop()
        await self.unload()
        self.config = load_config_file(self.config_path)
        await self.load()
        await self.start()

    def setup_skills(self, skills):
        """Call the setup function on the loaded skills.

        Iterates through all the skills which have been loaded and runs
        any setup functions which have been defined in the skill.

        Args:
            skills (list): A list of all the loaded skills.

        """
        if not skills:
            return

        for skill in skills:
            for func in skill["module"].__dict__.values():
                if isinstance(func, type) and issubclass(func, Skill) and func != Skill:
                    skill_obj = func(self, skill["config"])

                    for name in skill_obj.__dir__():
                        # pylint: disable=broad-except
                        # Getting an attribute of
                        # an object might raise any type of exceptions, for
                        # example within an external library called from an
                        # object property.  Since we are only interested in
                        # skill methods, we can safely ignore these.
                        try:
                            method = getattr(skill_obj, name)
                        except Exception:
                            continue

                        if hasattr(method, "skill"):
                            self.register_skill(method)

                    continue

                if hasattr(func, "skill"):
                    self.register_skill(func, skill["config"])

        with contextlib.suppress(AttributeError):
            for skill in skills:
                skill["module"].setup(self, self.config)

    def register_skill(self, skill, config=None):
        """Register a skill callable."""
        if config is not None:
            skill.config = config
        self.skills.append(skill)

    async def watch_paths(self):
        """Watch locally installed skill paths for file changes and reload on change.

        If a file within a locally installed skill is modified then opsdroid should be
        reloaded to pick up this change.

        When skills are loaded all local skills have their paths registered in
        ``self.reload_paths`` so we will watch those paths for changes.

        """

        async def watch_and_reload(opsdroid, path):
            async for _ in awatch(path, watcher_cls=PythonWatcher):
                await opsdroid.reload()

        if self.config.get("autoreload", False):
            _LOGGER.warning(
                _(
                    "Watching module files for changes. "
                    "Warning autoreload is an experimental feature."
                )
            )
            await asyncio.gather(
                *[watch_and_reload(self, path) for path in self.reload_paths]
            )

    async def train_parsers(self, skills):
        """Train the parsers.

        Args:
            skills (list): A list of all the loaded skills.

        """
        if "parsers" in self.modules:
            parsers = self.modules.get("parsers", {})
            rasanlu = get_parser_config("rasanlu", parsers)
            if rasanlu and rasanlu["enabled"]:
                await train_rasanlu(rasanlu, skills)

    async def setup_connectors(self, connectors):
        """Extract connectors from modules and register them in opsdroid.

        Args:
            connectors (list): A list of all the loaded connector modules.

        """
        for connector_module in connectors:
            for _, cls in connector_module["module"].__dict__.items():
                if (
                    isinstance(cls, type)
                    and issubclass(cls, Connector)
                    and cls is not Connector
                ):
                    connector = cls(connector_module["config"], self)
                    self.connectors.append(connector)

        if not self.connectors:
            self.critical("All connectors failed to load.", 1)

    async def start_connectors(self):
        """Start the connectors.

        Iterates through all the connectors parsed in the argument,
        spawns all that can be loaded, and keeps them open (listening).

        """
        await asyncio.gather(*[connector.connect() for connector in self.connectors])
        for connector in self.connectors:
            self.create_task(connector.listen())

    # pylint: disable=W0640
    @property
    def _connector_names(self):  # noqa: D401
        """Mapping of names to connector instances.

        Returns:
            names (list): A list of the names of connectors that are running.

        """
        if not self.connectors:
            raise ValueError("No connectors have been started")

        names = {}
        for connector in self.connectors:
            name = connector.config.get("name", connector.name)
            # Deduplicate any names
            if name in names:
                # Calculate the number of keys in names which start with name.
                n_key = len(list(filter(lambda x: x.startswith(name), names)))
                name += "_{}".format(n_key)
            names[name] = connector

        return names

    async def setup_databases(self, databases):
        """Extract database from modules and register them in opsdroid.

        Args:
            databases (list): A list of all the loaded database modules.

        """
        if not databases:
            self.memory.databases = [InMemoryDatabase()]
            return

        for database_module in databases:
            for name, cls in database_module["module"].__dict__.items():
                if (
                    isinstance(cls, type)
                    and issubclass(cls, Database)
                    and cls is not Database
                ):
                    _LOGGER.debug(_("Adding database: %s."), name)
                    database = cls(database_module["config"], opsdroid=self)
                    self.memory.databases.append(database)

    async def start_databases(self):
        """Start the databases.

        Iterates through all the database modules parsed
        in the argument, connects and starts them.

        """
        await asyncio.gather(
            *[database.connect() for database in self.memory.databases]
        )

    async def run_skill(self, skill, config, event):
        """Execute a skill.

        Attempts to run the skill parsed and provides other arguments to the skill if necessary.
        Also handles the exception encountered if th e

        Args:
            skill: name of the skill to be run.
            config: The configuration the skill must be loaded in.
            event: Message/event to be parsed to the chat service.

        """
        # pylint: disable=broad-except
        # We want to catch all exceptions coming from a skill module and not
        # halt the application. If a skill throws an exception it just doesn't
        # give a response to the user, so an error response should be given.
        try:
            if len(inspect.signature(skill).parameters.keys()) > 1:
                return await skill(self, config, event)
            else:
                return await skill(event)
        except Exception:
            _LOGGER.exception(
                _("Exception when running skill '%s'."), str(config["name"])
            )
            if event:
                await event.respond(
                    events.Message(_("Whoops there has been an error."))
                )
                await event.respond(events.Message(_("Check the log for details.")))

    async def get_ranked_skills(self, skills, message):
        """Take a message and return a ranked list of matching skills.

        Args:
            skills (list): List of all available skills.
            message (string): Context message to base the ranking of skills on.

        Returns:
            ranked_skills (list): List of all available skills sorted and ranked based on the score they muster when matched against the message parsed.

        """
        ranked_skills = []
        if isinstance(message, events.Message):
            ranked_skills += await parse_regex(self, skills, message)
            ranked_skills += await parse_format(self, skills, message)

        if "parsers" in self.modules:
            _LOGGER.debug(_("Processing parsers..."))
            parsers = self.modules.get("parsers", {})

            dialogflow = get_parser_config("dialogflow", parsers)
            if dialogflow and dialogflow["enabled"]:
                _LOGGER.debug(_("Checking dialogflow..."))
                ranked_skills += await parse_dialogflow(
                    self, skills, message, dialogflow
                )

            luisai = get_parser_config("luisai", parsers)
            if luisai and luisai["enabled"]:
                _LOGGER.debug(_("Checking luisai..."))
                ranked_skills += await parse_luisai(self, skills, message, luisai)

            sapcai = get_parser_config("sapcai", parsers)
            if sapcai and sapcai["enabled"]:
                _LOGGER.debug(_("Checking SAPCAI..."))
                ranked_skills += await parse_sapcai(self, skills, message, sapcai)

            witai = get_parser_config("witai", parsers)
            if witai and witai["enabled"]:
                _LOGGER.debug(_("Checking wit.ai..."))
                ranked_skills += await parse_witai(self, skills, message, witai)

            watson = get_parser_config("watson", parsers)
            if watson and watson["enabled"]:
                _LOGGER.debug(_("Checking IBM Watson..."))
                ranked_skills += await parse_watson(self, skills, message, watson)

            rasanlu = get_parser_config("rasanlu", parsers)
            if rasanlu and rasanlu["enabled"]:
                _LOGGER.debug(_("Checking Rasa NLU..."))
                ranked_skills += await parse_rasanlu(self, skills, message, rasanlu)

        return sorted(ranked_skills, key=lambda k: k["score"], reverse=True)

    def get_connector(self, name):
        """Get a connector object.

        Get a specific connector by name from the list of active connectors.

        Args:
            name (string): Name of the connector we want to access.

        Returns:
            connector (opsdroid.connector.Connector): An opsdroid connector.

        """
        try:
            [connector] = [
                connector for connector in self.connectors if connector.name == name
            ]
            return connector
        except ValueError:
            return None

    def get_database(self, name):
        """Get a database object.

        Get a specific database by name from the list of active databases.

        Args:
            name (string): Name of the database we want to access.

        Returns:
            database (opsdroid.database.Database): An opsdroid database.

        """
        try:
            [database] = [
                database for database in self.memory.databases if database.name == name
            ]
            return database
        except ValueError:
            return None

    def get_skill_instance(self, skill):
        """Get the parent instance of a skill.

        Skills in opsdroid are functions or bound methods of a class instance. For class based skills
        sometimes you may want to get the instance of the class the method is bound to. This helper
        will retrieve the instance for a method skill.

        Args:
            skill: The skill we want to get the instance for.

        Returns:
            The instance of the class or ``None`` if the skill is a function skill

        """
        while hasattr(skill, "__wrapped__"):
            skill = skill.__wrapped__
        if hasattr(skill, "__self__"):
            return skill.__self__
        else:
            return None

    async def _constrain_skills(self, skills, message):
        """Remove skills with contraints which prohibit them from running.

        Args:
            skills (list): A list of skills to be checked for constraints.
            message (opsdroid.events.Message): The message currently being
                parsed.

        Returns:
            list: A list of the skills which were not constrained.

        """
        return [
            skill
            for skill in skills
            if all(constraint(message) for constraint in skill.constraints)
        ]

    async def parse(self, event):
        """Parse a string against all skills.

        Args:
            event (String): The string to parsed against all available skills.

        Returns:
            tasks (list): Task that tells the skill which best matches the parsed event.

        """
        self.stats["messages_parsed"] = self.stats["messages_parsed"] + 1
        tasks = []
        tasks.append(self.eventloop.create_task(parse_always(self, event)))
        tasks.append(self.eventloop.create_task(parse_event_type(self, event)))
        if isinstance(event, events.Message):
            _LOGGER.debug(_("Parsing input: %s."), event)

            unconstrained_skills = await self._constrain_skills(self.skills, event)
            ranked_skills = await self.get_ranked_skills(unconstrained_skills, event)
            if ranked_skills:
                tasks.append(
                    self.eventloop.create_task(
                        self.run_skill(
                            ranked_skills[0]["skill"],
                            ranked_skills[0]["config"],
                            ranked_skills[0]["message"],
                        )
                    )
                )
        if len(tasks) == 2:  # no other skills ran other than 2 default ones
            tasks.append(self.eventloop.create_task(parse_catchall(self, event)))
        await asyncio.gather(*tasks)

        return tasks

    async def send(self, event):
        """Send an event.

        If ``event.connector`` is not set this method will use
        `OpsDroid.default_connector`. If ``event.connector`` is a string, it
        will be resolved to the name of the connectors configured in this
        instance.

        Args:
            event (opsdroid.events.Event): The event to send.

        """
        if isinstance(event.connector, str):
            event.connector = self._connector_names[event.connector]

        if not event.connector:
            event.connector = self.default_connector

        return await event.connector.send(event)

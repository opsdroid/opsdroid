"""Class for loading in modules to OpsDroid."""

# pylint: disable=too-many-branches

import contextlib
import importlib
import importlib.util
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from collections.abc import Mapping
from pkg_resources import iter_entry_points

from opsdroid.helper import (
    file_is_ipython_notebook,
    convert_ipynb_to_script,
    extract_gist_id,
)

from opsdroid.configuration import validate_configuration
from opsdroid.const import (
    DEFAULT_GIT_URL,
    MODULES_DIRECTORY,
    DEFAULT_MODULES_PATH,
    DEFAULT_MODULE_BRANCH,
    DEFAULT_MODULE_DEPS_PATH,
)


_LOGGER = logging.getLogger(__name__)


class Loader:
    """Class to load in config and modules."""

    def __init__(self, opsdroid):
        """Create object with opsdroid instance."""
        self.opsdroid = opsdroid
        self.modules_directory = None
        self.current_import_config = None
        _LOGGER.debug(_("Loaded loader."))

    @staticmethod
    def import_module_from_spec(module_spec):
        """Import from a given module spec and return imported module.

        Args:
            module_spec: ModuleSpec object containing name, loader, origin,
                submodule_search_locations, cached, and parent

        Returns:
            Module: Module imported from spec

        """
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module

    @staticmethod
    def import_module(config):
        """Import module namespace as variable and return it.

        Args:
            config: dict of config information related to the module

        Returns:
            Module: Module imported from config

        """
        # Try to import the module from various locations, return the first
        # successful import, or None if they all failed
        #
        # 1. check for entry point for installed module
        # 2. try to import the module directly off PYTHONPATH
        # 3. try to import a module with the given name in the module_path
        # 4. try to import the module_path itself

        if config.get("entrypoint"):
            _LOGGER.debug(
                _("Loading entry point-defined module for %s."), config["name"]
            )
            return config["entrypoint"].load()

        module_spec = None
        namespaces = [
            config["module"],
            config["module_path"] + "." + config["name"],
            config["module_path"],
        ]
        for namespace in namespaces:
            try:
                module_spec = importlib.util.find_spec(namespace)
                if module_spec:
                    break
            except (ImportError, AttributeError):
                continue

        if module_spec:
            try:
                module = Loader.import_module_from_spec(module_spec)
            except Exception as e:
                _LOGGER.error(
                    _("The following exception was raised while importing %s %s"),
                    config["type"],
                    config["module_path"],
                )
                _LOGGER.error(str(e))
            else:
                _LOGGER.debug(
                    _("Loaded %s: %s."), config["type"], config["module_path"]
                )
                return module

        _LOGGER.error(
            _("Failed to load %s: %s."), config["type"], config["module_path"]
        )
        return None

    @classmethod
    def check_cache(cls, config):
        """Remove module if 'no-cache' set in config.

        Args:
            config: dict of config information related to the module

        """
        if "no-cache" in config and config["no-cache"]:
            _LOGGER.debug(_("'no-cache' set, removing %s."), config["install_path"])
            cls.remove_cache(config)

        if "no-cache" not in config and cls._is_local_module(config):
            _LOGGER.debug(
                _(
                    "Removing cache for local module %s, set 'no-cache: false' to disable this."
                ),
                config["install_path"],
            )
            cls.remove_cache(config)

    @staticmethod
    def remove_cache(config):
        """Remove module cache.

        Args:
            config: dict of config information related to the module

        """
        if os.path.isdir(config["install_path"]):
            shutil.rmtree(config["install_path"])
        if os.path.isfile(config["install_path"] + ".py"):
            os.remove(config["install_path"] + ".py")

    @staticmethod
    def is_builtin_module(config):
        """Check if a module is a builtin.

        Args:
            config: dict of config information related to the module

        Returns:
            bool: False if the module is not builtin

        """
        try:
            return importlib.util.find_spec(
                "opsdroid.{module_type}.{module_name}".format(
                    module_type=config["type"], module_name=config["name"].lower()
                )
            )
        except ImportError:
            return False

    @staticmethod
    def build_module_import_path(config):
        """Generate the module import path from name and type.

        Args:
            config: dict of config information related to the module

        Returns:
            string: module import path

        """
        if config["is_builtin"]:
            return "opsdroid" + "." + config["type"] + "." + config["name"].lower()
        return MODULES_DIRECTORY + "." + config["type"] + "." + config["name"]

    def build_module_install_path(self, config):
        """Generate the module install path from name and type.

        Args:
            self: instance method
            config: dict of config information related to the module

        Returns:
            string: module install directory

        """
        return os.path.join(self.modules_directory, config["type"], config["name"])

    @staticmethod
    def git_clone(git_url, install_path, branch, key_path=None):
        """Clone a git repo to a location and wait for finish.

        Args:
            git_url: The url to the git repository
            install_path: Location where the git repository will be cloned
            branch: The branch to be cloned
            key_path: SSH Key for git repository

        """
        git_env = os.environ.copy()
        if key_path:
            git_env[
                "GIT_SSH_COMMAND"
            ] = f"ssh -i {key_path} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

        process = subprocess.Popen(
            ["git", "clone", "-b", branch, git_url, install_path],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=git_env,
        )
        Loader._communicate_process(process)

    @staticmethod
    def git_pull(repository_path):
        """Pull the current branch of git repo forcing fast forward.

        Args:
            repository_path: Path to the module's local repository

        """
        process = subprocess.Popen(
            ["git", "-C", repository_path, "pull", "--ff-only"],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        Loader._communicate_process(process)

    @staticmethod
    def pip_install_deps(requirements_path):
        """Pip install a requirements.txt file and wait for finish.

        Args:
            requirements_path: string holding the path to the requirements.txt
                file located in the module's local repository

        Returns:
            bool: True if the requirements.txt installs successfully

        """
        process = None
        command = [
            "pip",
            "install",
            "--target={}".format(DEFAULT_MODULE_DEPS_PATH),
            "--ignore-installed",
            "-r",
            requirements_path,
        ]

        try:
            process = subprocess.Popen(
                command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

        except FileNotFoundError:
            _LOGGER.debug(
                _("Couldn't find the command 'pip', trying again with command 'pip3'.")
            )

        try:
            command[0] = "pip3"
            process = subprocess.Popen(
                command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except FileNotFoundError:
            _LOGGER.debug(
                _("Couldn't find the command 'pip3', install of %s will be skipped."),
                str(requirements_path),
            )

        if not process:
            raise OSError(_("Pip and pip3 not found, exiting..."))

        Loader._communicate_process(process)
        return True

    @staticmethod
    def _communicate_process(process):
        for output in process.communicate():
            for line in output.splitlines():
                _LOGGER.debug(str(line).strip())

    @staticmethod
    def _load_intents(config):
        intent_file = os.path.join(config["install_path"], "intents.yml")
        if os.path.isfile(intent_file):
            with open(intent_file, "r") as intent_file_handle:
                intents = intent_file_handle.read()
                return intents
        else:
            return None

    def setup_modules_directory(self, config):
        """Create and configure the modules directory.

        Args:
            self: instance method
            config: dict of fields from configuration.yaml

        """
        module_path = config.get("module-path", DEFAULT_MODULES_PATH)
        sys.path.append(module_path)

        if not os.path.isdir(module_path):
            os.makedirs(module_path, exist_ok=True)

        self.modules_directory = os.path.join(module_path, MODULES_DIRECTORY)

        # Create modules directory if doesn't exist
        if not os.path.isdir(self.modules_directory):
            os.makedirs(self.modules_directory)

    def load_modules_from_config(self, config):
        """Load all module types based on config.

        Args:
            self: instance method
            config: dict of fields from configuration.yaml

        Returns:
            dict: containing connector, database, and skills
                fields from configuration.yaml

        """
        _LOGGER.debug(_("Loading modules from config..."))

        self.setup_modules_directory(config)

        connectors, databases, parsers, skills = None, None, None, None

        if "databases" in config.keys() and config["databases"]:
            databases = self._load_modules("database", config["databases"])
        else:
            _LOGGER.warning(
                _(
                    "No databases in configuration. This will cause skills which store things in "
                    "memory to lose data when opsdroid is restarted."
                )
            )
        if "parsers" in config.keys() and config["parsers"]:
            parsers = self._load_modules("parsers", config["parsers"])

        if "skills" in config.keys() and config["skills"]:
            skills = self._load_modules("skill", config["skills"])

        if "connectors" in config.keys() and config["connectors"]:
            connectors = self._load_modules("connector", config["connectors"])
        else:
            self.opsdroid.critical(
                _("No connectors in configuration, at least 1 required"), 1
            )

        return {
            "connectors": connectors,
            "databases": databases,
            "parsers": parsers,
            "skills": skills,
        }

    def setup_module_config(self, modules, module, modules_type, entry_points):
        """Set up configuration for module.

        When setting up the configuration for a module we assign a lot
        of key:value pairs into a config dictionary.

        Also we might want to load from a configuration file an item that
        is just a string rather than a mapping object so we do a check and
        update the config as appropriate.

        We also need to update the config file with the rest of the config params.
        Since modules can be Key: { key: value } or key: None, we suppress the
        TypeError exception which is given when we try to use .get() on a None type,
        .

        Args:
            modules (dict): Dictionary containing all modules
            module (dict): Module to be configured
            modules_type (str): Type of module being loaded
            entry_points (dict): name of possible entry points.

        Returns:
            dict: configuration containing all the set key:values

        """
        config = module
        config = {} if config is None else config

        if not isinstance(config, Mapping):
            config = {"name": module, "module": ""}
        else:
            config["name"] = module["name"]
            config["module"] = module.get("module", "")

        with contextlib.suppress(TypeError, AttributeError):
            config.update(modules.get(module))

        config["type"] = modules_type
        config["enabled"] = True
        config["entrypoint"] = entry_points.get(config["name"], None)
        config["is_builtin"] = self.is_builtin_module(config)
        config["module_path"] = self.build_module_import_path(config)
        config["install_path"] = self.build_module_install_path(config)

        if "branch" not in config:
            config["branch"] = DEFAULT_MODULE_BRANCH

        return config

    def _load_modules(self, modules_type, modules):
        """Install and load modules.

        Args:
            self: instance method
            modules_type (str): Type of module being loaded
            modules (dict): Dictionary containing all modules

        Returns:
            list: modules and their config information

        """
        _LOGGER.debug(_("Loading %s modules..."), modules_type)
        loaded_modules = list()

        if not os.path.isdir(DEFAULT_MODULE_DEPS_PATH):
            os.makedirs(DEFAULT_MODULE_DEPS_PATH)
        sys.path.append(DEFAULT_MODULE_DEPS_PATH)

        # entry point group naming scheme: opsdroid_ + module type plural,
        # eg. "opsdroid_databases"
        epname = "opsdroid_{}s".format(modules_type)
        entry_points = {ep.name: ep for ep in iter_entry_points(group=epname)}
        for epname in entry_points:
            _LOGGER.debug(
                _("Found installed package for %s '%s' support."), modules_type, epname
            )

        for module in modules:
            config = self.setup_module_config(
                modules, module, modules_type, entry_points
            )

            # If the module isn't builtin, or isn't already on the
            # python path, install it
            if not (config["is_builtin"] or config["module"] or config["entrypoint"]):
                # Remove module for reinstall if no-cache set
                self.check_cache(config)

                # Install or update module
                if not self._is_module_installed(config):
                    self._install_module(config)
                else:
                    self._update_module(config)

            # Import module
            self.current_import_config = config
            module = self.import_module(config)

            # Suppress exception if module doesn't contain CONFIG_SCHEMA
            with contextlib.suppress(AttributeError):
                config = validate_configuration(config, module.CONFIG_SCHEMA)

            # Load intents
            intents = self._load_intents(config)

            if module is not None:
                loaded_modules.append(
                    {"module": module, "config": config, "intents": intents}
                )
            else:
                _LOGGER.error(_("Module %s failed to import."), config["name"])
        return loaded_modules

    def _install_module(self, config):
        """Install a module.

        Args:
            self: instance method
            config: dict of module config fields

        """
        _LOGGER.debug(_("Installing %s..."), config["name"])

        if self._is_local_module(config):
            self._install_local_module(config)
        elif self._is_gist_module(config):
            self._install_gist_module(config)
        else:
            self._install_git_module(config)

        if self._is_module_installed(config):
            _LOGGER.debug(
                _("Installed %s to %s."), config["name"], config["install_path"]
            )
        else:
            _LOGGER.error(_("Install of %s failed."), config["name"])

        self._install_module_dependencies(config)

    def _update_module(self, config):
        """Update a module.

        Args:
            self: instance method
            config: dict of module config fields

        """
        _LOGGER.debug(_("Updating %s..."), config["name"])

        if self._is_local_module(config):
            _LOGGER.debug(_("Local modules are not updated, skipping."))
            return

        self.git_pull(config["install_path"])
        self._install_module_dependencies(config)

    @staticmethod
    def _is_module_installed(config):
        return os.path.isdir(config["install_path"]) or os.path.isfile(
            config["install_path"] + ".py"
        )

    @staticmethod
    def _is_local_module(config):
        return "path" in config

    @staticmethod
    def _is_gist_module(config):
        return "gist" in config

    def _install_module_dependencies(self, config):
        """Install the dependencies of the module.

        Args:
            self: instance method
            config: dict of the module config fields

        Returns:
            bool: True if installation succeeds

        """
        if config.get("no-dep", False):
            _LOGGER.debug(
                _(
                    "'no-dep' set in configuration, skipping the install of dependencies."
                )
            )
            return None

        if os.path.isfile(os.path.join(config["install_path"], "requirements.txt")):
            self.pip_install_deps(
                os.path.join(config["install_path"], "requirements.txt")
            )
            return True

        _LOGGER.debug(_("Couldn't find the file requirements.txt, skipping."))
        return None

    def _install_git_module(self, config):
        """Install a module from a git repository.

        Args:
            self: instance method
            config: dict of module config fields

        """
        if config is not None and "repo" in config:
            git_url = config["repo"]
        else:
            git_url = DEFAULT_GIT_URL + config["type"] + "-" + config["name"] + ".git"

        if any(prefix in git_url for prefix in ["http", "https", "ssh", "git@"]):
            # TODO Test if url or ssh path exists
            # TODO Handle github authentication
            _LOGGER.info(_("Cloning %s from remote repository."), config["name"])
            key_path = config.get("key_path", None)
            self.git_clone(git_url, config["install_path"], config["branch"], key_path)
        else:
            if os.path.isdir(git_url):
                _LOGGER.debug(_("Cloning %s from local repository."), config["name"])
                self.git_clone(git_url, config["install_path"], config["branch"])
            else:
                _LOGGER.error(_("Could not find local git repo %s."), git_url)

    def _install_local_module(self, config):
        """Install a module from a local path.

        Args:
            config: dict of module config fields

        """
        installed = False
        config["path"] = os.path.expanduser(config["path"])

        installdir, _ = os.path.split(config["install_path"])
        if not os.path.isdir(installdir):
            os.makedirs(installdir, exist_ok=True)

        if os.path.isdir(config["path"]):
            shutil.copytree(config["path"], config["install_path"])
            installed = True

        if os.path.isfile(config["path"]):
            os.makedirs(config["install_path"], exist_ok=True)
            init_path = os.path.join(config["install_path"], "__init__.py")
            if file_is_ipython_notebook(config["path"]):
                convert_ipynb_to_script(config["path"], init_path)
            else:
                shutil.copyfile(config["path"], init_path)
            installed = True

        if not installed:
            _LOGGER.error("Failed to install from %s.", str(config["path"]))
        else:
            self.opsdroid.reload_paths.append(config["path"])

    def _install_gist_module(self, config):
        """Install a module from gist path.

        Args:
            self: instance method
            config: dict of module config fields

        """
        gist_id = extract_gist_id(config["gist"])

        # Get the content of the gist
        req = urllib.request.Request("https://api.github.com/gists/{}".format(gist_id))
        cont = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        python_files = [
            cont["files"][file]
            for file in cont["files"]
            if ".ipynb" in cont["files"][file]["filename"]
            or ".py" in cont["files"][file]["filename"]
        ]

        # We only support one skill file in a gist for now.
        #
        # TODO: Add support for multiple files. Could be particularly
        # useful for including a requirements.txt file.
        skill_content = python_files[0]["content"]
        extension = os.path.splitext(python_files[0]["filename"])[1]

        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=extension
        ) as skill_file:
            skill_file.write(skill_content)
            skill_file.flush()

            # Set the path in the config
            config["path"] = skill_file.name

            # Run local install
            self._install_local_module(config)

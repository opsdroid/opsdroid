"""Class for loading in modules to OpsDroid."""

import logging
import os
import sys
import shutil
import subprocess
import importlib
import re
import yaml
from opsdroid.const import (
    DEFAULT_GIT_URL, MODULES_DIRECTORY, DEFAULT_MODULES_PATH,
    DEFAULT_MODULE_BRANCH, DEFAULT_CONFIG_PATH, EXAMPLE_CONFIG_FILE,
    DEFAULT_MODULE_DEPS_PATH)


_LOGGER = logging.getLogger(__name__)


class Loader:
    """Class to load in config and modules."""

    def __init__(self, opsdroid):
        """Create object with opsdroid instance."""
        self.opsdroid = opsdroid
        self.modules_directory = None
        self.current_import_config = None
        _LOGGER.debug("Loaded loader")

    @staticmethod
    def import_module(config):
        """Import module namespace as variable and return it."""
        try:
            module = importlib.import_module(
                config["module_path"] + "." + config["name"])
            _LOGGER.debug("Loaded " + config["type"] + ": " +
                          config["module_path"])
            return module
        except ImportError as error:
            _LOGGER.debug("Failed to load " + config["type"] +
                          " " + config["module_path"] + "." + config["name"])
            _LOGGER.debug(error)

        try:
            module = importlib.import_module(
                config["module_path"])
            _LOGGER.debug("Loaded " + config["type"] + ": " +
                          config["module_path"])
            return module
        except ImportError as error:
            _LOGGER.debug("Failed to load " + config["type"] +
                          " " + config["module_path"])
            _LOGGER.debug(error)

        _LOGGER.error("Failed to load " + config["type"] +
                      " " + config["module_path"])
        return None

    @staticmethod
    def check_cache(config):
        """Remove module if 'no-cache' set in config."""
        if "no-cache" in config \
                and config["no-cache"]:
            _LOGGER.debug("'no-cache' set, removing " + config["install_path"])
            if os.path.isdir(config["install_path"]):
                shutil.rmtree(config["install_path"])
            if os.path.isfile(config["install_path"] + ".py"):
                os.remove(config["install_path"] + ".py")

    def build_module_path(self, path_type, config):
        """Generate the module path from name and type."""
        if path_type == "import":
            return MODULES_DIRECTORY + "." + config["type"] + \
                        "." + config["name"]
        elif path_type == "install":
            return self.modules_directory + "/" + config["type"] + \
                        "/" + config["name"]

    @staticmethod
    def git_clone(git_url, install_path, branch):
        """Clone a git repo to a location and wait for finish."""
        process = subprocess.Popen(["git", "clone", "-b", branch,
                                    git_url, install_path], shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        for output in process.communicate():
            if output != "":
                for line in output.splitlines():
                    _LOGGER.debug(str(line).strip())
        process.wait()

    @staticmethod
    def pip_install_deps(requirements_path):
        """Pip install a requirements.txt file and wait for finish."""
        process = subprocess.Popen(["pip", "install",
                                    "--target={}".format(
                                        DEFAULT_MODULE_DEPS_PATH),
                                    "--ignore-installed",
                                    "-r", requirements_path],
                                   shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        for output in process.communicate():
            if output != "":
                for line in output.splitlines():
                    _LOGGER.debug(str(line).strip())
        process.wait()

    @staticmethod
    def create_default_config(config_path):
        """Create a default config file based on the included example."""
        _LOGGER.info("Creating %s.", config_path)
        config_dir, _ = os.path.split(config_path)
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir)
        shutil.copyfile(EXAMPLE_CONFIG_FILE, config_path)
        return config_path

    def _reload_modules(self, modules):
        for module in modules:
            self.current_import_config = module["config"]
            importlib.reload(module["module"])

    def load_config_file(self, config_paths):
        """Load a yaml config file from path."""
        config_path = ""
        for possible_path in config_paths:
            if not os.path.isfile(possible_path):
                _LOGGER.debug("Config file " + possible_path +
                              " not found")
            else:
                config_path = possible_path
                break

        if not config_path:
            _LOGGER.info("No configuration files found.")
            config_path = self.create_default_config(DEFAULT_CONFIG_PATH)

        env_var_pattern = re.compile(r'^\$([A-Z_]*)$')
        yaml.add_implicit_resolver("!envvar", env_var_pattern)

        def envvar_constructor(loader, node):
            """Yaml parser for env vars."""
            value = loader.construct_scalar(node)
            [env_var] = env_var_pattern.match(value).groups()
            return os.environ[env_var]

        yaml.add_constructor('!envvar', envvar_constructor)

        try:
            with open(config_path, 'r') as stream:
                _LOGGER.info("Loaded config from %s", config_path)
                return yaml.load(stream)
        except yaml.YAMLError as error:
            self.opsdroid.critical(error, 1)
        except FileNotFoundError as error:
            self.opsdroid.critical(str(error), 1)

    def setup_modules_directory(self, config):
        """Create and configure the modules directory."""
        module_path = os.path.expanduser(
            config.get("module-path", DEFAULT_MODULES_PATH))
        sys.path.append(module_path)

        if not os.path.isdir(module_path):
            os.makedirs(module_path, exist_ok=True)

        self.modules_directory = os.path.join(module_path, MODULES_DIRECTORY)

        # Create modules directory if doesn't exist
        if not os.path.isdir(self.modules_directory):
            os.makedirs(self.modules_directory)

    def load_modules_from_config(self, config):
        """Load all module types based on config."""
        _LOGGER.debug("Loading modules from config")

        self.setup_modules_directory(config)

        connectors, databases, skills = None, None, None

        if 'databases' in config.keys():
            databases = self._load_modules('database', config['databases'])
        else:
            _LOGGER.warning("No databases in configuration")

        if 'skills' in config.keys():
            skills = self._load_modules('skill', config['skills'])
            self.opsdroid.skills = []
            self._reload_modules(skills)

        else:
            self.opsdroid.critical(
                "No skills in configuration, at least 1 required", 1)

        if 'connectors' in config.keys():
            connectors = self._load_modules('connector', config['connectors'])
        else:
            self.opsdroid.critical(
                "No connectors in configuration, at least 1 required", 1)

        return connectors, databases, skills

    def _load_modules(self, modules_type, modules):
        """Install and load modules."""
        _LOGGER.debug("Loading " + modules_type + " modules")
        loaded_modules = []

        if not os.path.isdir(DEFAULT_MODULE_DEPS_PATH):
            os.makedirs(DEFAULT_MODULE_DEPS_PATH)
        sys.path.append(DEFAULT_MODULE_DEPS_PATH)

        for module in modules:

            # Set up module config
            config = module
            config = {} if config is None else config
            config["name"] = module["name"]
            config["type"] = modules_type
            config["module_path"] = self.build_module_path("import", config)
            config["install_path"] = self.build_module_path("install", config)
            if "branch" not in config:
                config["branch"] = DEFAULT_MODULE_BRANCH

            # Remove module for reinstall if no-cache set
            self.check_cache(config)

            # Install module
            self._install_module(config)

            # Import module
            self.current_import_config = config
            module = self.import_module(config)
            if module is not None:
                loaded_modules.append({
                    "module": module,
                    "config": config})
            else:
                _LOGGER.error(
                    "Module " + config["name"] + " failed to import")

        return loaded_modules

    def _install_module(self, config):
        # pylint: disable=R0201
        """Install a module."""
        _LOGGER.debug("Installing " + config["name"])

        if os.path.isdir(config["install_path"]) or \
                os.path.isfile(config["install_path"] + ".py"):
            # TODO Allow for updating or reinstalling of modules
            _LOGGER.debug("Module " + config["name"] +
                          " already installed, skipping")
            return

        if "path" in config:
            self._install_local_module(config)
        else:
            self._install_git_module(config)

        if os.path.isdir(config["install_path"]):
            _LOGGER.debug("Installed " + config["name"] +
                          " to " + config["install_path"])
        else:
            _LOGGER.debug("Install of " + config["name"] + " failed")

        # Install module dependancies
        if os.path.isfile(config["install_path"] + "/requirements.txt"):
            self.pip_install_deps(config["install_path"] +
                                  "/requirements.txt")

    def _install_git_module(self, config):
        """Install a module from a git repository."""
        if config is not None and "repo" in config:
            git_url = config["repo"]
        else:
            git_url = DEFAULT_GIT_URL + config["type"] + \
                        "-" + config["name"] + ".git"

        if any(prefix in git_url for prefix in ["http", "https", "ssh"]):
            # TODO Test if url or ssh path exists
            # TODO Handle github authentication
            _LOGGER.debug("Cloning from remote repository")
            self.git_clone(git_url, config["install_path"],
                           config["branch"])
        else:
            if os.path.isdir(git_url):
                _LOGGER.debug("Cloning from local repository")
                self.git_clone(git_url, config["install_path"],
                               config["branch"])
            else:
                _LOGGER.debug("Could not find local git repo " + git_url)

    @staticmethod
    def _install_local_module(config):
        """Install a module from a local path."""
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
            shutil.copyfile(config["path"], config["install_path"] +
                            "/__init__.py")
            installed = True

        if not installed:
            _LOGGER.error("Failed to install from " + config["path"])

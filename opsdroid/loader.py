"""Class for loading in modules to OpsDroid."""

import importlib
import importlib.util
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from collections import Mapping

import yaml

from opsdroid.helper import (
    move_config_to_appdir, file_is_ipython_notebook,
    convert_ipynb_to_script, extract_gist_id)
from opsdroid.const import (
    DEFAULT_GIT_URL, MODULES_DIRECTORY, DEFAULT_MODULES_PATH,
    DEFAULT_MODULE_BRANCH, DEFAULT_CONFIG_PATH, EXAMPLE_CONFIG_FILE,
    DEFAULT_MODULE_DEPS_PATH, PRE_0_12_0_ROOT_PATH, DEFAULT_ROOT_PATH)


_LOGGER = logging.getLogger(__name__)


class Loader:
    """Class to load in config and modules."""

    def __init__(self, opsdroid):
        """Create object with opsdroid instance."""
        self.opsdroid = opsdroid
        self.modules_directory = None
        self.current_import_config = None
        _LOGGER.debug(_("Loaded loader"))

    @staticmethod
    def import_module_from_spec(module_spec):
        """Import from a given module spec and return imported module."""
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module

    @staticmethod
    def import_module(config):
        """Import module namespace as variable and return it."""
        # Check if the module can be imported and proceed with import

        # Proceed only if config.name is specified
        # and parent module can be imported
        if config["name"] and importlib.util.find_spec(config["module_path"]):
            module_spec = importlib.util.find_spec(config["module_path"] +
                                                   "." + config["name"])
            if module_spec:
                module = Loader.import_module_from_spec(module_spec)
                _LOGGER.debug(_("Loaded %s: %s"), config["type"],
                              config["module_path"])
                return module

        module_spec = importlib.util.find_spec(config["module_path"])
        if module_spec:
            module = Loader.import_module_from_spec(module_spec)
            _LOGGER.debug(_("Loaded %s: %s"),
                          config["type"], config["module_path"])
            return module

        _LOGGER.error(_("Failed to load %s: %s"),
                      config["type"], config["module_path"])

        return None

    @staticmethod
    def check_cache(config):
        """Remove module if 'no-cache' set in config."""
        if "no-cache" in config \
                and config["no-cache"]:
            _LOGGER.debug(_("'no-cache' set, removing %s"),
                          config["install_path"])
            if os.path.isdir(config["install_path"]):
                shutil.rmtree(config["install_path"])
            if os.path.isfile(config["install_path"] + ".py"):
                os.remove(config["install_path"] + ".py")

    @staticmethod
    def is_builtin_module(config):
        """Check if a module is a builtin."""
        try:
            return importlib.util.find_spec(
                'opsdroid.{module_type}.{module_name}'.format(
                    module_type=config["type"],
                    module_name=config["name"]
                )
            )
        except ImportError:
            return False

    @staticmethod
    def build_module_import_path(config):
        """Generate the module import path from name and type."""
        if config["is_builtin"]:
            return "opsdroid" + "." + config["type"] + \
                "." + config["name"]
        return MODULES_DIRECTORY + "." + config["type"] + \
            "." + config["name"]

    def build_module_install_path(self, config):
        """Generate the module install path from name and type."""
        return os.path.join(self.modules_directory,
                            config["type"],
                            config["name"])

    @staticmethod
    def git_clone(git_url, install_path, branch):
        """Clone a git repo to a location and wait for finish."""
        process = subprocess.Popen(["git", "clone", "-b", branch,
                                    git_url, install_path], shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        Loader._communicate_process(process)

    @staticmethod
    def git_pull(repository_path):
        """Pull the current branch of git repo forcing fast forward."""
        process = subprocess.Popen(["git", "-C", repository_path,
                                    "pull", "--ff-only"],
                                   shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        Loader._communicate_process(process)

    @staticmethod
    def pip_install_deps(requirements_path):
        """Pip install a requirements.txt file and wait for finish."""
        process = None
        command = ["pip", "install",
                   "--target={}".format(DEFAULT_MODULE_DEPS_PATH),
                   "--ignore-installed", "-r", requirements_path]

        try:
            process = subprocess.Popen(command,
                                       shell=False,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

        except FileNotFoundError:
            _LOGGER.debug(_("Couldn't find the command 'pip', "
                            "trying again with command 'pip3'"))

        try:
            command[0] = "pip3"
            process = subprocess.Popen(command,
                                       shell=False,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        except FileNotFoundError:
            _LOGGER.debug(_("Couldn't find the command 'pip3', "
                            "install of %s will be skipped."),
                          str(requirements_path))

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
        intent_file = os.path.join(config["install_path"], "intents.md")
        if os.path.isfile(intent_file):
            with open(intent_file, 'r') as intent_file_handle:
                intents = intent_file_handle.read()
                return intents
        else:
            return None

    @staticmethod
    def create_default_config(config_path):
        """Create a default config file based on the included example."""
        _LOGGER.info("Creating %s.", config_path)
        config_dir, _ = os.path.split(config_path)
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir)
        shutil.copyfile(EXAMPLE_CONFIG_FILE, config_path)
        return config_path

    def load_config_file(self, config_paths):
        """Load a yaml config file from path."""
        config_path = ""
        for possible_path in config_paths:
            if not os.path.isfile(possible_path):
                _LOGGER.debug(_("Config file %s not found."), possible_path)
            else:
                config_path = possible_path
                break

        if not config_path:
            try:
                move_config_to_appdir(PRE_0_12_0_ROOT_PATH, DEFAULT_ROOT_PATH)
            except FileNotFoundError:
                _LOGGER.info(_("No configuration files found. "
                               "Creating %s"), DEFAULT_CONFIG_PATH)
            config_path = self.create_default_config(DEFAULT_CONFIG_PATH)

        env_var_pattern = re.compile(r'^\$([A-Z_]*)$')
        yaml.add_implicit_resolver("!envvar", env_var_pattern)

        def envvar_constructor(loader, node):
            """Yaml parser for env vars."""
            value = loader.construct_scalar(node)
            [env_var] = env_var_pattern.match(value).groups()
            return os.environ[env_var]

        def include_constructor(loader, node):
            """Add a yaml file to be loaded inside another."""
            main_yaml_path = os.path.split(stream.name)[0]
            included_yaml = os.path.join(main_yaml_path,
                                         loader.construct_scalar(node))

            with open(included_yaml, 'r') as included:
                return yaml.safe_load(included)

        yaml.add_constructor('!envvar', envvar_constructor)
        yaml.add_constructor('!include', include_constructor)

        try:
            with open(config_path, 'r') as stream:
                _LOGGER.info(_("Loaded config from %s."), config_path)
                return yaml.load(stream)
        except yaml.YAMLError as error:
            self.opsdroid.critical(error, 1)
        except FileNotFoundError as error:
            self.opsdroid.critical(str(error), 1)

    def setup_modules_directory(self, config):
        """Create and configure the modules directory."""
        module_path = config.get("module-path", DEFAULT_MODULES_PATH)
        sys.path.append(module_path)

        if not os.path.isdir(module_path):
            os.makedirs(module_path, exist_ok=True)

        self.modules_directory = os.path.join(module_path, MODULES_DIRECTORY)

        # Create modules directory if doesn't exist
        if not os.path.isdir(self.modules_directory):
            os.makedirs(self.modules_directory)

    def load_modules_from_config(self, config):
        """Load all module types based on config."""
        _LOGGER.debug(_("Loading modules from config..."))

        self.setup_modules_directory(config)

        connectors, databases, skills = None, None, None

        if 'databases' in config.keys() and config['databases']:
            databases = self._load_modules('database', config['databases'])
        else:
            _LOGGER.warning(_("No databases in configuration."
                              "This will cause skills which store things in "
                              "memory to lose data when opsdroid is "
                              "restarted."))

        if 'skills' in config.keys() and config['skills']:
            skills = self._load_modules('skill', config['skills'])

        else:
            self.opsdroid.critical(_(
                "No skills in configuration, at least 1 required"), 1)

        if 'connectors' in config.keys() and config['connectors']:
            connectors = self._load_modules('connector', config['connectors'])
        else:
            self.opsdroid.critical(_(
                "No connectors in configuration, at least 1 required"), 1)

        return connectors, databases, skills

    def _load_modules(self, modules_type, modules):
        """Install and load modules."""
        _LOGGER.debug(_("Loading %s modules..."), modules_type)
        loaded_modules = []

        if not os.path.isdir(DEFAULT_MODULE_DEPS_PATH):
            os.makedirs(DEFAULT_MODULE_DEPS_PATH)
        sys.path.append(DEFAULT_MODULE_DEPS_PATH)

        for module in modules:

            # Set up module config
            config = module
            config = {} if config is None else config

            # We might load from a configuration file an item that is just
            # a string, rather than a mapping object
            if not isinstance(config, Mapping):
                config = {}
                config["name"] = module
            else:
                config["name"] = module['name']
            config["type"] = modules_type
            config["is_builtin"] = self.is_builtin_module(config)
            config["module_path"] = self.build_module_import_path(config)
            config["install_path"] = self.build_module_install_path(config)
            if "branch" not in config:
                config["branch"] = DEFAULT_MODULE_BRANCH

            if not config["is_builtin"]:
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

            # Load intents
            intents = self._load_intents(config)

            if module is not None:
                loaded_modules.append({
                    "module": module,
                    "config": config,
                    "intents": intents})
            else:
                _LOGGER.error(_(
                    "Module %s failed to import."), config["name"])

        return loaded_modules

    def _install_module(self, config):
        """Install a module."""
        _LOGGER.debug(_("Installing %s..."), config["name"])

        if self._is_local_module(config):
            self._install_local_module(config)
        elif self._is_gist_module(config):
            self._install_gist_module(config)
        else:
            self._install_git_module(config)

        if self._is_module_installed(config):
            _LOGGER.debug(_("Installed %s to %s"),
                          config["name"], config["install_path"])
        else:
            _LOGGER.error(_("Install of %s failed."), config["name"])

        self._install_module_dependencies(config)

    def _update_module(self, config):
        """Update a module."""
        _LOGGER.debug(_("Updating %s..."), config["name"])

        if self._is_local_module(config):
            _LOGGER.debug(_("Local modules are not updated, skipping."))
            return

        self.git_pull(config["install_path"])
        self._install_module_dependencies(config)

    @staticmethod
    def _is_module_installed(config):
        return os.path.isdir(config["install_path"]) or \
            os.path.isfile(config["install_path"] + ".py")

    @staticmethod
    def _is_local_module(config):
        return "path" in config

    @staticmethod
    def _is_gist_module(config):
        return "gist" in config

    def _install_module_dependencies(self, config):
        if config.get('no-dep', False):
            _LOGGER.debug(_("'no-dep' set in configuration, skipping the "
                            "install of dependencies."))
            return None

        if os.path.isfile(os.path.join(
                config["install_path"], "requirements.txt")):
            self.pip_install_deps(os.path.join(config["install_path"],
                                               "requirements.txt"))
            return True

        _LOGGER.debug("Couldn't find the file requirements.txt, "
                      "skipping.")
        return None

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
            _LOGGER.info(_("Cloning %s from remote repository"),
                         config["name"])
            self.git_clone(git_url, config["install_path"],
                           config["branch"])
        else:
            if os.path.isdir(git_url):
                _LOGGER.debug(_("Cloning %s from local repository"),
                              config["name"])
                self.git_clone(git_url, config["install_path"],
                               config["branch"])
            else:
                _LOGGER.error(_("Could not find local git repo %s"), git_url)

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
            init_path = os.path.join(config["install_path"], "__init__.py")
            if file_is_ipython_notebook(config["path"]):
                convert_ipynb_to_script(config["path"], init_path)
            else:
                shutil.copyfile(config["path"], init_path)
            installed = True

        if not installed:
            _LOGGER.error("Failed to install from %s",
                          str(config["path"]))

    def _install_gist_module(self, config):
        gist_id = extract_gist_id(config['gist'])

        # Get the content of the gist
        req = urllib.request.Request(
            "https://api.github.com/gists/{}".format(gist_id))
        cont = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        python_files = [cont["files"][file] for file in cont["files"]
                        if '.ipynb' in cont["files"][file]["filename"]
                        or '.py' in cont["files"][file]["filename"]]

        # We only support one skill file in a gist for now.
        #
        # TODO: Add support for mutliple files. Could be particularly
        # useful for including a requirements.txt file.
        skill_content = python_files[0]["content"]
        extension = os.path.splitext(python_files[0]["filename"])[1]

        with tempfile.NamedTemporaryFile('w',
                                         delete=False,
                                         suffix=extension) as skill_file:
            skill_file.write(skill_content)
            skill_file.flush()

            # Set the path in the config
            config["path"] = skill_file.name

            # Run local install
            self._install_local_module(config)

"""Class for loading in modules to OpsDroid."""

import logging
import os
import shutil
import subprocess
import importlib
import yaml
from opsdroid.const import (
    DEFAULT_GIT_URL, MODULES_DIRECTORY, DEFAULT_MODULE_BRANCH)


class Loader:
    """Class to load in config and modules."""

    def __init__(self, opsdroid):
        """Setup object with opsdroid instance."""
        self.opsdroid = opsdroid
        logging.debug("Loaded loader")

    @staticmethod
    def import_module(config):
        """Import module namespace as variable and return it."""
        try:
            module = importlib.import_module(
                config["path"] + "." + config["name"])
            logging.debug("Loading " + config["type"] + ": " + config["name"])
            return module
        except ImportError as error:
            logging.error("Failed to load " + config["type"] +
                          " " + config["name"])
            logging.error(error)
            return None

    @staticmethod
    def check_cache(config):
        """Remove module if 'no-cache' set in config."""
        if "no-cache" in config \
                and config["no-cache"] \
                and os.path.isdir(config["install_path"]):
            logging.debug("'no-cache' set, removing " + config["install_path"])
            shutil.rmtree(config["install_path"])

    @staticmethod
    def build_module_path(path_type, config):
        """Generate the module path from name and type."""
        if path_type == "import":
            return MODULES_DIRECTORY + "." + config["type"] + \
                        "." + config["name"]
        elif path_type == "install":
            return MODULES_DIRECTORY + "/" + config["type"] + \
                        "/" + config["name"]

    @staticmethod
    def git_clone(git_url, install_path, branch):
        """Clone a git repo to a location and wait for finish."""
        process = subprocess.Popen(["git", "clone", "-b", branch,
                                    git_url, install_path], shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.wait()

    @staticmethod
    def pip_install_deps(requirements_path):
        """Pip install a requirements.txt file and wait for finish."""
        process = subprocess.Popen(["pip", "install", "-r", requirements_path],
                                   shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        for output in process.communicate():
            if output != "":
                for line in output.splitlines():
                    logging.debug(str(line).strip())
        process.wait()

    def load_config_file(self, config_paths):
        """Load a yaml config file from path."""
        config_path = ""
        for possible_path in config_paths:
            if not os.path.isfile(possible_path):
                logging.warning("Config file " + possible_path +
                                " not found", 1)
            else:
                config_path = possible_path
                break

        if not config_path:
            self.opsdroid.critical("No configuration files found", 1)

        try:
            with open(config_path, 'r') as stream:
                return yaml.load(stream)
        except yaml.YAMLError as error:
            self.opsdroid.critical(error, 1)
        except FileNotFoundError as error:
            self.opsdroid.critical(str(error), 1)

    def load_config(self, config):
        """Load all module types based on config."""
        logging.debug("Loading modules from config")

        connectors, databases, skills = None, None, None

        if 'databases' in config.keys():
            databases = self._load_modules('database', config['databases'])
        else:
            logging.warning("No databases in configuration")

        if 'skills' in config.keys():
            skills = self._load_modules('skill', config['skills'])
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
        logging.debug("Loading " + modules_type + " modules")
        loaded_modules = []

        # Create modules directory if doesn't exist
        if not os.path.isdir(MODULES_DIRECTORY):
            os.makedirs(MODULES_DIRECTORY)

        for module_name in modules.keys():

            # Set up module config
            config = modules[module_name]
            config = {} if config is None else config
            config["name"] = module_name
            config["type"] = modules_type
            config["path"] = self.build_module_path("import", config)
            config["install_path"] = self.build_module_path("install", config)
            if "branch" not in config:
                config["branch"] = DEFAULT_MODULE_BRANCH

            # Remove module for reinstall if no-cache set
            self.check_cache(config)

            # Install module
            self._install_module(config)

            # Import module
            module = self.import_module(config)
            if module is not None:
                loaded_modules.append({
                    "module": module,
                    "config": config})

        return loaded_modules

    def _install_module(self, config):
        # pylint: disable=R0201
        """Install a module."""
        logging.debug("Installing " + config["name"])

        if os.path.isdir(config["install_path"]):
            # TODO Allow for updating or reinstalling of modules
            logging.debug("Module " + config["name"] +
                          " already installed, skipping")
        else:
            if config is not None and "repo" in config:
                git_url = config["repo"]
            else:
                git_url = DEFAULT_GIT_URL + config["type"] + \
                            "-" + config["name"] + ".git"

            if any(prefix in git_url for prefix in ["http", "https", "ssh"]):
                # TODO Test if url or ssh path exists
                # TODO Handle github authentication
                self.git_clone(git_url, config["install_path"],
                               config["branch"])
            else:
                if os.path.isdir(git_url):
                    self.git_clone(git_url, config["install_path"],
                                   config["branch"])
                else:
                    logging.debug("Could not find local git repo " + git_url)

            if os.path.isdir(config["install_path"]):
                logging.debug("Installed " + config["name"] +
                              " to " + config["install_path"])
            else:
                logging.debug("Install of " + config["name"] + " failed")

            # Install module dependancies
            if os.path.isfile(config["install_path"] + "/requirements.txt"):
                self.pip_install_deps(config["install_path"] +
                                      "/requirements.txt")

"""Class for loading in modules to OpsDroid."""

import logging
import os
import shutil
import subprocess
import importlib
import pip
import yaml
from opsdroid.const import (
    DEFAULT_GIT_URL, MODULES_DIRECTORY, DEFAULT_MODULE_BRANCH)


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


def build_module_path(mod_type, mod_name):
    """Generate the module path from name and type."""
    return MODULES_DIRECTORY + "." + mod_type + "." + mod_name


def git_clone(git_url, install_path, branch):
    """Clone a git repo to a location and wait for finish."""
    process = subprocess.Popen(["git", "clone", "-b", branch,
                                git_url, install_path], shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    process.wait()


class Loader:
    """Class to load in config and modules."""

    def __init__(self, opsdroid):
        """Setup object with opsdroid instance."""
        self.opsdroid = opsdroid
        logging.debug("Loaded loader")

    def load_config_file(self, config_path):
        """Load a yaml config file from path."""
        if not os.path.isfile(config_path):
            self.opsdroid.critical("Config file " + config_path +
                                   " not found", 1)

        try:
            with open(config_path, 'r') as stream:
                return yaml.load(stream)
        except yaml.YAMLError as error:
            self.opsdroid.critical(error, 1)
        except FileNotFoundError as error:
            self.opsdroid.critical(error, 1)

    def load_config(self, config):
        """Load all module types based on config."""
        logging.debug("Loading modules from config")

        if 'databases' in config.keys():
            # TODO: Implement database modules
            self._load_modules('database', config['databases'])
        else:
            logging.warning("No databases in configuration")

        if 'skills' in config.keys():
            self._setup_modules(
                self._load_modules('skill', config['skills'])
            )
        else:
            self.opsdroid.critical(
                "No skills in configuration, at least 1 required", 1)

        if 'connectors' in config.keys():
            self.opsdroid.start_connectors(
                self._load_modules('connector', config['connectors']))
        else:
            self.opsdroid.critical(
                "No connectors in configuration, at least 1 required", 1)

    def _load_modules(self, modules_type, modules):
        """Load modules."""
        logging.debug("Loading " + modules_type + " modules")
        loaded_modules = []

        if not os.path.isdir(MODULES_DIRECTORY):
            os.makedirs(MODULES_DIRECTORY)

        for module_name in modules.keys():

            # Set up module config
            config = modules[module_name]
            if config is None:
                config = {}
            config["name"] = module_name
            config["type"] = modules_type
            config["path"] = build_module_path(config["type"], config["name"])
            config["install_path"] = MODULES_DIRECTORY + "/" + \
                config["type"] + "/" + config["name"]

            if "branch" not in config:
                config["branch"] = DEFAULT_MODULE_BRANCH

            # Remove module for reinstall if no-cache set
            if "no-cache" in config \
                    and config["no-cache"] \
                    and os.path.isdir(config["install_path"]):
                logging.debug("'no-cache' set, removing " + config["path"])
                shutil.rmtree(config["install_path"])

            # Install module
            self._install_module(
                config["name"], config["type"],
                config, config["install_path"])

            # Import module
            loaded_modules.append({
                "module": import_module(config),
                "config": config})

        return loaded_modules

    def _setup_modules(self, modules):
        """Call the setup function on the passed in modules."""
        for module in modules:
            module["module"].setup(self.opsdroid)

    def _install_module(self, name, mod_type, config, install_path):
        # pylint: disable=R0201
        """Install a module."""
        logging.debug("Installing " + name)

        if os.path.isdir(install_path):
            # TODO Allow for updating or reinstalling of modules
            logging.debug("Module " + name +
                          " already installed, skipping")
        else:
            if config is not None and "repo" in config:
                git_url = config["repo"]
            else:
                git_url = DEFAULT_GIT_URL + mod_type + \
                            "-" + name + ".git"

            if any(x in git_url for x in ["http", "https", "ssh"]):
                # TODO Test if url or ssh path exists
                # TODO Handle github authentication
                git_clone(git_url, install_path, config["branch"])
            else:
                if os.path.isdir(git_url):
                    git_clone(git_url, install_path, config["branch"])
                else:
                    logging.debug("Could not find local git repo " + git_url)

            if os.path.isdir(install_path):
                logging.debug("Installed " + name +
                              " to " + install_path)
            else:
                logging.debug("Install of " + name + " failed ")

            # Install module dependancies
            if os.path.isfile(install_path + "/requirements.txt"):
                pip.main(["install", "-r", install_path + "/requirements.txt"])

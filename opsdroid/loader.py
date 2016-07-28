""" Class for loading in modules to OpsDroid """

import logging
import sys
import os
import subprocess
import pip
import shutil
import yaml
import importlib
from opsdroid.const import DEFAULT_GIT_URL, MODULES_DIRECTORY, DEFAULT_MODULE_BRANCH

class Loader:
    def __init__(self, opsdroid):
        self.opsdroid = opsdroid
        logging.debug("Loaded loader")

    def load_config_file(self, config_path):
        """ Load a yaml config file from path """
        if not os.path.isfile(config_path):
            self.opsdroid.critical("Config file " + config_path + " not found", 1)

        try:
            with open(config_path, 'r') as stream:
                return(yaml.load(stream))
        except yaml.YAMLError as e:
            self.opsdroid.critical(e, 1)
        except FileNotFoundError as e:
            self.opsdroid.critical(e, 1)

    def load_config(self, config):
        """ Load all module types based on config """
        logging.debug("Loading modules from config")

        if 'databases' in config.keys():
            # TODO: Implement database modules
            self._load_modules('database', config['databases'])
        else:
            logging.warn("No databases in configuration")

        if 'skills' in config.keys():
            self._setup_modules(
                self._load_modules('skill', config['skills'])
            )
        else:
            self.opsdroid.critical("No skills in configuration, at least 1 required", 1)

        if 'connectors' in config.keys():
            self.opsdroid.start_connectors(self._load_modules('connector', config['connectors']))
        else:
            self.opsdroid.critical("No connectors in configuration, at least 1 required", 1)

    def _load_modules(self, modules_type, modules):
        """ Load modules """
        logging.debug("Loading " + modules_type + " modules")
        loaded_modules = []

        if not os.path.isdir(MODULES_DIRECTORY):
            os.makedirs(MODULES_DIRECTORY)

        for module_name in modules.keys():

            if modules[module_name] == None:
                modules[module_name] = {}

            module_path = self._build_module_path(modules_type, module_name)
            install_path = MODULES_DIRECTORY + "/" + modules_type + "/" + module_name

            if "branch" not in modules[module_name]:
                modules[module_name]["branch"] = DEFAULT_MODULE_BRANCH

            # Remove module for reinstall if no-cache set
            if "no-cache" in modules[module_name] \
                        and modules[module_name]["no-cache"] == True \
                        and os.path.isdir(install_path):
                logging.debug("'no-cache' set, removing module " + module_path)
                shutil.rmtree(install_path)

            # Install module
            self._install_module(module_name, modules_type, modules[module_name], install_path)

            # Import module
            try:
                logging.debug("Module path: " + module_path)
                module = importlib.import_module(module_path + "." + module_name)
                logging.debug("Loading " + modules_type + ": " + module_name)
                loaded_modules.append({"module": module, "config": modules[module_name]})
            except ImportError as e:
                logging.error("Failed to load " + modules_type + " " + module_name)
                logging.error(e)

        return loaded_modules

    def _setup_modules(self, modules):
        """ Call the setup function on the passed in modules """
        for module in modules:
            module["module"].setup(self.opsdroid)

    def _install_module(self, module_name, module_type, module_config, install_path):
        """ Install a module """
        logging.debug("Installing " + module_name)

        if os.path.isdir(install_path):
            # TODO Allow for updating or reinstalling of modules
            logging.debug("Module " + module_name + " already installed, skipping")
        else:
            if module_config != None and "repo" in module_config:
                git_url = module_config["repo"]
            else:
                git_url = DEFAULT_GIT_URL + module_type + "-" + module_name + ".git"

            if any(x in git_url for x in ["http", "https", "ssh"]):
                # TODO Test if url or ssh path exists
                # TODO Handle github authentication
                self._git_clone(git_url, install_path, module_config["branch"])
            else:
                if os.path.isdir(git_url):
                    self._git_clone(git_url, install_path, module_config["branch"])
                else:
                    logging.debug("Could not find local git repo " + git_url)

            if os.path.isdir(install_path):
                logging.debug("Installed " + module_name + " to " + install_path)
            else:
                logging.debug("Install of " + module_name + " failed ")

            # Install module dependancies
            if os.path.isfile(install_path + "/requirements.txt"):
                pip.main(["install", "-r", install_path + "/requirements.txt"])

    def _build_module_path(self, mod_type, mod_name):
        """ Generate the module path from name and type """
        return MODULES_DIRECTORY + "." + mod_type + "." + mod_name

    def _git_clone(self, git_url, install_path, branch):
        """ Clone a git repo to a location and wait for finish """
        p = subprocess.Popen(["git", "clone", "-b", branch, git_url, install_path], shell=False,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()

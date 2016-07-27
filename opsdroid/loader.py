import logging
import sys
import os
import yaml
import importlib
import git
from opsdroid.const import DEFAULT_GIT_URL

class Loader:
    def __init__(self, opsdroid):
        self.opsdroid = opsdroid
        logging.debug("Loaded loader")

    def load_config_file(self, config_path):
        """ Load a yaml config file from path """
        with open(config_path, 'r') as stream:
            try:
                return(yaml.load(stream))
            except yaml.YAMLError as exc:
                self.opsdroid.critical(exc, 1)

    def load_config(self, config):
        """ Load all module types based on config """
        logging.debug("Loading config")

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
        for module_name in modules.keys():
            try:
                module_path = self._build_module_path(modules_type, module_name)
                logging.debug("Module path: " + module_path)
                self._install_module(module_name, modules_type, modules[module_name])
                module = importlib.import_module(module_path + "." + module_name)
                logging.debug("Loading " + modules_type + ": " + module_name)
                loaded_modules.append(module)
            except ImportError:
                logging.error("Failed to load " + modules_type + " " + module_name)
        return loaded_modules

    def _setup_modules(self, modules):
        """ Call the setup function on the passed in modules """
        for module in modules:
            module.setup(self.opsdroid)

    def _install_module(self, module_name, module_type, module_config):
        """ Install a module """
        logging.debug("Installing " + module_name)
        install_path = "modules/" + module_type + "/" + module_name
        if os.path.isdir(install_path):
            logging.debug("Module " + module_name + " already installed, skipping")
        else:
            if module_config != None and "repo" in module_config:
                git_url = module_config["repo"]
            else:
                git_url = DEFAULT_GIT_URL + module_type + "-" + module_name + ".git"
            try:
                if any(x in git_url for x in ["http", "https", "ssh"]):
                    # TODO test if url or ssh path exists
                    git.Repo.clone_from(git_url, install_path)
                else:
                    if os.path.isdir(git_url):
                        git.Repo.clone_from(git_url, install_path)
            except git.exc.GitCommandError as e:
                print(e)

    def _build_module_path(self, mod_type, mod_name):
        return "modules." + mod_type + "." + mod_name

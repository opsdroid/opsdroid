import os
import shutil
import sys
import logging
from voluptuous import Schema, MultipleInvalid, ALLOW_EXTRA
import yaml


from opsdroid.helper import move_config_to_appdir

from opsdroid.const import (
    DEFAULT_CONFIG_PATH,
    EXAMPLE_CONFIG_FILE,
    PRE_0_12_0_ROOT_PATH,
    DEFAULT_ROOT_PATH,
)
from opsdroid.configuration.constructors import (
    envvar_constructor,
    include_constructor,
    env_var_pattern,
)


_LOGGER = logging.getLogger(__name__)


def create_default_config(config_path):
    """Create a default config file based on the example config file.

    If we can't find any configuration.yaml, we will pull the whole
    example_configuration.yaml and use this file as the configuration.

    Args:
        config_path: String containing the path to configuration.yaml
            default install location

    Returns:
        str: path to configuration.yaml default install location

    """
    _LOGGER.info(_("Creating %s."), config_path)
    config_dir, _ = os.path.split(config_path)
    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)
    shutil.copyfile(EXAMPLE_CONFIG_FILE, config_path)
    return config_path


def get_config_path(config_paths):
    """Get the path to configuration.yaml.

    Opsdroid configuration.yaml can be located in different paths.
    With this function, we will go through all of the possible paths and
    return the correct path.

    Before version 0.12.0 opsdroid would be located at "~/.opsdroid", we
    have moved to appdirs. If we were unable to get the path we will try to
    find the configuration.yaml file on "~/.opsdroid" and move it to the right
    path for the OS in question (DEFAULT_ROOT_PATH) - which is a path got by
    appdirs.

    Finally, if we don't have any configuration.yaml we will just create one using
    the example configuration file.

    Args:
        config_paths: List containing all the possible config paths.

    Returns:
        str: Path to the configuration file.

    """
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
            _LOGGER.info(
                _("No configuration files found. Creating %s"), DEFAULT_CONFIG_PATH
            )
        config_path = create_default_config(DEFAULT_CONFIG_PATH)

    return config_path


def load_config_file(config_paths):
    """Load a yaml config file from path.

    Args:
        config_paths: List of paths to configuration.yaml files

    Returns:
        dict: Dict containing config fields

    """

    try:
        yaml_loader = yaml.CSafeLoader
    except AttributeError:
        yaml_loader = yaml.SafeLoader

    config_path = get_config_path(config_paths)

    yaml_loader.add_implicit_resolver("!envvar", env_var_pattern, first="$")
    yaml_loader.add_constructor("!envvar", envvar_constructor)
    yaml_loader.add_constructor("!include", include_constructor)

    schema_test = {
        "logging": {"level": str, "console": bool},
        "welcome-message": bool,
        "connectors": [{"name": str, "token": str, "access-token": str}],
        "skills": [{"name": str}],
    }
    schema = Schema(schema_test, extra=ALLOW_EXTRA)

    try:
        with open(config_path, "r") as stream:
            _LOGGER.info(_("Loaded config from %s."), config_path)
            data = yaml.load(stream, Loader=yaml_loader)
            schema(data)

            return data

    except MultipleInvalid as error:
        _LOGGER.critical("Configuration contains an error - %s", error)
        sys.exit(1)

    except ValueError as error:
        _LOGGER.critical(error)
        sys.exit(1)

    except yaml.YAMLError as error:
        _LOGGER.critical(error)
        sys.exit(1)

    except FileNotFoundError as error:
        _LOGGER.critical(error)
        sys.exit(1)

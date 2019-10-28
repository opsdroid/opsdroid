"""Yaml constructors to give more functionalities to the configuration."""

import appdirs
import os
import re
import yaml

from opsdroid.const import NAME

env_var_pattern = re.compile(r"^\$([A-Z_]*)$")


def envvar_constructor(loader, node):
    """Yaml parser for env vars."""
    value = loader.construct_scalar(node)
    [env_var] = env_var_pattern.match(value).groups()
    return os.environ[env_var]


def include_constructor(loader, node):
    """Add a yaml file to be loaded inside another."""
    main_yaml_path = appdirs.user_config_dir(NAME, appauthor=False)
    included_yaml = os.path.join(main_yaml_path, loader.construct_scalar(node))

    with open(included_yaml, "r") as included:
        return yaml.load(included, Loader=yaml.CSafeLoader)

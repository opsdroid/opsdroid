"""Helper functions to use within OpsDroid."""

import os
import stat
import shutil
import logging

from opsdroid.const import PRE_0_12_0_CONFIG_PATH, DEFAULT_CONFIG_PATH

_LOGGER = logging.getLogger(__name__)


def get_opsdroid():
    """Return the running opsdroid instance."""
    from opsdroid.core import OpsDroid
    if len(OpsDroid.instances) == 1:
        return OpsDroid.instances[0]

    return None


def del_rw(action, name, exc):
    """Error handler for removing read only files."""
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)


def move_config_to_appdir():
    """Move configuration.yaml from ~/.opsdroid to
    system configuration directory."""
    if os.path.isfile(PRE_0_12_0_CONFIG_PATH):
        shutil.copyfile(PRE_0_12_0_CONFIG_PATH, DEFAULT_CONFIG_PATH)
        _LOGGER.info("Configuration file copied from {} to {} "
                     "run opsdroid --c to edit the config "
                     "file.".format(PRE_0_12_0_CONFIG_PATH, DEFAULT_CONFIG_PATH))
        os.remove(PRE_0_12_0_CONFIG_PATH)

"""Helper functions to use within OpsDroid."""

import os
import stat
import shutil
import logging
import filecmp

from opsdroid.const import DEFAULT_ROOT_PATH, PRE_0_12_0_ROOT_PATH

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

# This is meant to provide backwards compatibility for versions
# prior to  0.12.0 in the future this will probably be deleted


def move_config_to_appdir():
    """Copy any file with .yaml extension to new appdir location."""
    yaml_files = [file for file in os.listdir(PRE_0_12_0_ROOT_PATH)
                  if '.yaml' in file[-5:]]

    if not os.path.isdir(DEFAULT_ROOT_PATH):
        os.mkdir(DEFAULT_ROOT_PATH)

    for file in yaml_files:
        original_file = os.path.join(PRE_0_12_0_ROOT_PATH, file)
        copied_file = os.path.join(DEFAULT_ROOT_PATH, file)
        shutil.copyfile(original_file, copied_file)
        _LOGGER.info(_('File %s copied from %s to %s '
                       'run opsdroid -e to edit the '
                       'main config file'), file,
                     PRE_0_12_0_ROOT_PATH, DEFAULT_ROOT_PATH)
        if filecmp.cmp(original_file, copied_file):
            os.remove(original_file)

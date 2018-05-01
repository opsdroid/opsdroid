"""Helper functions to use within OpsDroid."""

import os
import stat
import shutil
import logging
import filecmp

_LOGGER = logging.getLogger(__name__)


def get_opsdroid():
    """This method return an opsdroid instance

    Returns:
        object: opsdroid instance.
    """
    from opsdroid.core import OpsDroid
    if len(OpsDroid.instances) == 1:
        return OpsDroid.instances[0]

    return None


def del_rw(action, name, exc):
    """This method return an error handler for removing.
        This method allow users to read only files.

        to write
    """
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)

# This is meant to provide backwards compatibility for versions
# prior to  0.12.0 in the future this will probably be deleted


def move_config_to_appdir(src, dst):
    """Copy any .yaml extension in "src" to "dst" and remove from "src"."""
    yaml_files = [file for file in os.listdir(src)
                  if '.yaml' in file[-5:]]

    if not os.path.isdir(dst):
        os.mkdir(dst)

    for file in yaml_files:
        original_file = os.path.join(src, file)
        copied_file = os.path.join(dst, file)
        shutil.copyfile(original_file, copied_file)
        _LOGGER.info(_('File %s copied from %s to %s '
                       'run opsdroid -e to edit the '
                       'main config file'), file,
                     src, dst)
        if filecmp.cmp(original_file, copied_file):
            os.remove(original_file)

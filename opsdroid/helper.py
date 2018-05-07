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

        Raises:
            KeyError : Raises an exception
"""
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)

# This is meant to provide backwards compatibility for versions
# prior to  0.12.0 in the future this will probably be deleted


def move_config_to_appdir(src, dst):
    """ This method allows to make copy of files with .yaml extension
        from  "src" folder to "dst" folder and remove the current file in "src".

    Args:
        src (str): path file.
        dst (str): destination path
    
    Attributes:
        msg (str):  File 'my_file.yaml' copied from '/path/src/ to '/past/dst/'.
        code (int): run opsdroid -e to edit the  main config file.
     
    Examples:
        src : source path with .yaml file '/path/src/my_file.yaml.
        dst : destination folder to paste the .yaml files '/path/dst/.
    """
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

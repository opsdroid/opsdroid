"""Helper functions to use within OpsDroid."""

import os
import stat
import shutil
import logging
import filecmp

import nbformat
from nbconvert import PythonExporter

_LOGGER = logging.getLogger(__name__)


def get_opsdroid():
    """Return the running opsdroid instance.

    Returns:
        object: opsdroid instance.

    """
    from opsdroid.core import OpsDroid
    if len(OpsDroid.instances) == 1:
        return OpsDroid.instances[0]

    return None


def del_rw(action, name, exc):
    """Error handler for removing read only files.

    Args:
        action: the function that raised the exception
        name: path name passed to the function (path and file name)
        exc: exception information return by sys.exc_info()

    Raises:
        OsError : If the file to be removed is a directory.

    """
    os.chmod(name, stat.S_IWRITE)
    os.remove(name)

# This is meant to provide backwards compatibility for versions
# prior to  0.12.0 in the future this will probably be deleted


def move_config_to_appdir(src, dst):
    """Copy any .yaml extension in "src" to "dst" and remove from "src".

    Args:
        src (str): path file.
        dst (str): destination path.

    Logging:
        info (str): File 'my_file.yaml' copied from '/path/src/
                       to '/past/dst/' run opsdroid -e to edit
                       the  main config file.

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


def file_is_ipython_notebook(path):
    """Check whether a file is an iPython Notebook.

    Args:
        path (str): path to the file.

    Examples:
        path : source path with .ipynb file '/path/src/my_file.ipynb.

    """
    return path.lower().endswith('.ipynb')


def convert_ipynb_to_script(notebook_path, output_path):
    """Convert an iPython Notebook to a python script.

    Args:
        notebook_path (str): path to the notebook file.
        output_path (str): path to the script file destination.

    Examples:
        notebook_path : source path with .ipynb file '/path/src/my_file.ipynb.
        output_path : destination path with .py file '/path/src/my_file.py.

    """
    with open(notebook_path, 'r') as notebook_path_handle:
        raw_notebook = notebook_path_handle.read()
        notebook = nbformat.reads(raw_notebook, as_version=4)
        script, _ = PythonExporter().from_notebook_node(notebook)
        with open(output_path, 'w') as output_path_handle:
            output_path_handle.write(script)


def extract_gist_id(gist_string):
    """Extract the gist ID from a url.

    Will also work if simply passed an ID.

    Args:
        gist_string (str): Gist URL.

    Returns:
        string: The gist ID.

    Examples:
        gist_string : Gist url 'https://gist.github.com/{user}/{id}'.

    """
    return gist_string.split("/")[-1]

"""Helper functions to use within OpsDroid."""

import datetime
import warnings
import os
import stat
import logging
import json

import nbformat
from nbconvert import PythonExporter

_LOGGER = logging.getLogger(__name__)


# pylint: disable=inconsistent-return-statements
def get_opsdroid():
    """Return the running opsdroid instance.

    Returns:
        object: opsdroid instance.

    """
    from opsdroid.core import OpsDroid

    if len(OpsDroid.instances) == 1:
        return OpsDroid.instances[0]


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
# prior to  0.16.0 in the future this will be deleted


def convert_dictionary(modules):
    """Convert dictionary to new format.

    We iterate over all the modules in the list and change the dictionary
    to be in the format 'name_of_module: { config_params}'

    Args:
        modules (list): List of dictionaries that contain the module configuration

    Return:
        List: New modified list following the new format.

    """
    config = dict()

    if isinstance(modules, list):
        _LOGGER.warning(
            "Opsdroid has a new configuration format since version 0.17.0. Please read on how to migrate in the documentation at https://docs.opsdroid.dev/en/stable/configuration.html#migrate-to-new-configuration-layout."
        )
        for module in modules:
            module_copy = module.copy()
            del module_copy["name"]

            if module.get("access-token") or module.get("api-token"):
                _LOGGER.warning(
                    _(
                        "Configuration param for %s has been deprecated in favor of 'token', please update your config."
                    ),
                    module["name"],
                )
                module_copy["token"] = module.get("access-token") or module.get(
                    "api-token"
                )

            config[module["name"]] = module_copy

        return config
    else:
        return modules


def update_pre_0_17_config_format(config):
    """Update each configuration param that contains 'name'.

    We decided to ditch the name param and instead divide each module by it's name.
    This change was due to validation issues. Now instead of a list of dictionaries
    without any pointer to what they are, we are using the name of the module and then a
    dictionary containing the configuration params for said module.

    Args:
        config (dict): Dictionary containing config got from configuration.yaml

    Returns:
        dict: updated configuration.

    """
    updated_config = {}
    for config_type, modules in config.items():
        if config_type in ("parsers", "connectors", "skills", "databases"):
            updated_config[config_type] = convert_dictionary(modules)

    config.update(updated_config)

    return config


def file_is_ipython_notebook(path):
    """Check whether a file is an iPython Notebook.

    Args:
        path (str): path to the file.

    Examples:
        path : source path with .ipynb file '/path/src/my_file.ipynb.

    """
    return path.lower().endswith(".ipynb")


def convert_ipynb_to_script(notebook_path, output_path):
    """Convert an iPython Notebook to a python script.

    Args:
        notebook_path (str): path to the notebook file.
        output_path (str): path to the script file destination.

    Examples:
        notebook_path : source path with .ipynb file '/path/src/my_file.ipynb.
        output_path : destination path with .py file '/path/src/my_file.py.

    """
    with open(notebook_path, "r") as notebook_path_handle:
        raw_notebook = notebook_path_handle.read()
        notebook = nbformat.reads(raw_notebook, as_version=4)
        script, _ = PythonExporter().from_notebook_node(notebook)
        with open(output_path, "w") as output_path_handle:
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


def add_skill_attributes(func):
    """Add the attributes which makes a function a skill.

    Args:
        func (func): Skill function.

    Returns:
        func: The skill function with the new attributes.

    """
    if not hasattr(func, "skill"):
        func.skill = True
    if not hasattr(func, "matchers"):
        func.matchers = []
    if not hasattr(func, "constraints"):
        func.constraints = []
    return func


def get_parser_config(name, modules):
    """Get parser from modules list.

    After the change to the configuration we are adding the "enabled" flag to each
    active module, this allows us to disable to module if there is any problem with
    it. This helper method helps getting the config from the list of active parsers.

    Args:
        name (string): Name of the parser to be fetched.
        modules (list): List of all active modules.

    Returns:
        dict or None: The module config or None if not found.

    """
    if modules:
        for parser in modules:
            if parser["config"]["name"] == name:
                return parser["config"]
    return None


def get_config_option(options, config, found, not_found):
    """Get config details and return useful information to list active modules.

    When we list modules we have to do a lot of search and get, this function serves as an
    helper to get all the needed information to show in a list format. Since we are using
    different formats and need to get 3 different details from the config we will either
    return them or use the placeholder from `not_found`.

    Args:
        options(list): list of all possible options to search in config.
        config(dict): This will be a section of the configuration (connectors, parsers, skills, etc).
        found(str, bool): Expected text if option exists in config.
        not_found(str): expected text if option doesn't exist in config.

    """
    try:
        for option in options:
            if config.get(option):
                return found, option, config.get(option)
        return not_found, not_found, not_found
    except (TypeError, AttributeError):
        return not_found, not_found, not_found


class JSONEncoder(json.JSONEncoder):
    """A extended JSONEncoder class.

    This class is customised JSONEncoder class which helps to convert
    dict to JSON. The datetime objects are converted to dict with fields
    as keys.

    """

    # pylint: disable=method-hidden
    # See https://github.com/PyCQA/pylint/issues/414 for reference

    serializers = {}

    def default(self, o):
        """Convert the given datetime object to dict.

        Args:
            o (object): The datetime object to be marshalled.

        Returns:
            dict (object): A dict with datatime object data.

        Example:
            A dict which is returned after marshalling::

                {
                    "__class__": "datetime",
                    "year": 2018,
                    "month": 10,
                    "day": 2,
                    "hour": 0,
                    "minute": 41,
                    "second": 17,
                    "microsecond": 74644
                }

        """
        marshaller = self.serializers.get(type(o), super(JSONEncoder, self).default)
        return marshaller(o)


class JSONDecoder:
    """A JSONDecoder class.

    This class will convert dict containing datetime values
    to datetime objects.

    """

    decoders = {}

    def __call__(self, dct):
        """Convert given dict to datetime objects.

        Args:
            dct (object): A dict containing datetime values and class type.

        Returns:
            object or dct: The datetime object for given dct, or dct if
                             respective class decoder is not found.

        Example:
            A datetime object returned after decoding::

                datetime.datetime(2018, 10, 2, 0, 41, 17, 74644)

        """
        if dct.get("__class__") in self.decoders:
            return self.decoders[dct["__class__"]](dct)
        return dct


def register_json_type(type_cls, fields, decode_fn):
    """Register JSON types.

    This method will register the serializers and decoders for the
    JSONEncoder and JSONDecoder classes respectively.

    Args:
        type_cls (object): A datetime object.
        fields (list): List of fields used to store data in dict.
        decode_fn (object): A lambda function object for decoding.

    """
    type_name = type_cls.__name__
    JSONEncoder.serializers[type_cls] = lambda obj: dict(
        __class__=type_name, **{field: getattr(obj, field) for field in fields}
    )
    JSONDecoder.decoders[type_name] = decode_fn


register_json_type(
    datetime.datetime,
    ["year", "month", "day", "hour", "minute", "second", "microsecond"],
    lambda dct: datetime.datetime(
        dct["year"],
        dct["month"],
        dct["day"],
        dct["hour"],
        dct["minute"],
        dct["second"],
        dct["microsecond"],
    ),
)

register_json_type(
    datetime.date,
    ["year", "month", "day"],
    lambda dct: datetime.date(dct["year"], dct["month"], dct["day"]),
)

register_json_type(
    datetime.time,
    ["hour", "minute", "second", "microsecond"],
    lambda dct: datetime.time(
        dct["hour"], dct["minute"], dct["second"], dct["microsecond"]
    ),
)


class TimeoutException(RuntimeError):
    """Raised when a loop times out."""


class Timeout:
    """A timeout object for use in ``while True`` loops instead of ``True``.

    Create an instance of this class before beginning an infinite loop and
    call ``run()`` instead of ``True``.

    Parameters
    ----------
    timeout: int
        Seconds before loop should timeout.

    error_message: str
        Error message to raise in an exception if timeout occurs.

    warn: bool
        Only raise a warning instead of a TimeoutException.

        Default ``False``.

    Examples
    --------
    >>> timeout = Timeout(10, "Oh no! We timed out.")
    >>> while timeout.run():
    ...     time.sleep(1)  # Will timeout after 10 iterations
    TimeoutException: Oh no! We timed out.

    You can also pass an exception to raise if you are supressing for a set
    amount of time.

    >>> timeout = Timeout(10, "Oh no! We timed out.")
    >>> while timeout.run():
    ...     try:
    ...         some_function_that_raises()
    ...         break
    ...     except Exception as e:
    ...         timeout.set_exception(e)
    ...         time.sleep(1)  # Will timeout after 10 iterations
    Exception: The exception from ``some_function_that_raises``

    """

    def __init__(self, timeout, error_message, warn=False):
        """Create a timeout object."""
        self.start = None
        self.running = False
        self.timeout = timeout
        self.error_message = error_message
        self.warn = warn
        self.exception = TimeoutException(self.error_message)

    def run(self):
        """Run the timeout.

        This method when called repeatedly will return ``True`` until the
        timeout has elapsed. It will then raise or return ``False``.
        """
        if not self.running:
            self.start = datetime.datetime.now()
            self.running = True

        if (
            self.start + datetime.timedelta(seconds=self.timeout)
            < datetime.datetime.now()
        ):
            if self.warn:
                warnings.warn(self.error_message)
                return False
            else:
                raise self.exception
        return True

    def set_exception(self, e):
        """Modify the default timeout exception.

        This would be useful if you are trying something repeatedly but if it
        never succeeds before the timeout you want to raise the exception from
        the thing you are trying rather than a TimeoutException.
        """
        self.exception = e

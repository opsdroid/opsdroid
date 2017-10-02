"""Helper functions to use within OpsDroid."""
import re
import requests


def get_opsdroid():
    """Return the running opsdroid instance."""
    from opsdroid.core import OpsDroid
    if len(OpsDroid.instances) == 1:
        return OpsDroid.instances[0]

    return None


def get_version():
    request = requests.get('https://pypi.python.org/pypi/opsdroid')
    version = re.findall('[0-9]\.[0-9]\.[0-9]', request.text)
    return version[0]

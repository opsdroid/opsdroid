"""Helper functions to use within OpsDroid."""

import os
import stat


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

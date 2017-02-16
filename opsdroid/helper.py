"""Helper functions to use within OpsDroid."""


def get_opsdroid():
    """Return the running opsdroid instance."""
    from opsdroid.core import OpsDroid
    if len(OpsDroid.instances) == 1:
        return OpsDroid.instances[0]
    else:
        return None

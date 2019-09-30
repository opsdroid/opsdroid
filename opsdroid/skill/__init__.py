"""Base class for class-based skills."""
from functools import wraps


def _skill_decorator(func):
    @wraps(func)
    def decorated_skill(*args, **kwargs):
        return func(*args, **kwargs)

    decorated_skill.config = func.__self__.config

    return decorated_skill


class Skill:
    """A skill prototype to use when creating classy skills."""

    # pylint: disable=too-few-public-methods
    def __init__(self, opsdroid, config, *args, **kwargs):
        """Create the skill.

        Set some basic properties from the skill.

        Args:
            opsdroid (OpsDroid): The running opsdroid instance pointer.
            config (dict): The config for this database specified in the
                           `configuration.yaml` file.

        """
        super().__init__()

        self.opsdroid = opsdroid
        self.config = config

        for name in self.__dir__():
            # pylint: disable=broad-except
            # Getting an attribute of an object
            # might raise any type of exceptions, for example within an
            # external library called from an object  property.  Since we are
            # only interested in skill methods, we can safely ignore these.
            try:
                method = getattr(self, name)
            except Exception:
                continue

            if hasattr(method, "matchers"):
                setattr(self, name, _skill_decorator(method))

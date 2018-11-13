"""Base class for class-based skills
"""
from functools import wraps


def _skill_decorator(func):
    @wraps(func)
    def decorated_skill(*args, **kwargs):
        return func(*args, **kwargs)

    decorated_skill.config = func.__self__.config

    return decorated_skill

class Skill:
    def __init__(self, opsdroid, config, *args, **kwargs):
        super(Skill, self).__init__()

        self.opsdroid = opsdroid
        self.config = config

        for name in self.__dir__():
            try:
                method = getattr(self, name)
            except Exception:
                continue

            if hasattr(method, 'matchers'):
                setattr(self, name, _skill_decorator(method))

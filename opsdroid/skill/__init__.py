"""Base class for class-based skills
"""
from opsdroid.matchers import add_skill_attributes

class Skill:
    def __init__(self, opsdroid, config, *args, **kwargs):
        super(Skill, self).__init__()

        self.opsdroid = opsdroid
        self.config = config

        for attr in self.__dir__():
            try:
                method = getattr(self, attr)
            except Exception:
                continue

            for decor_params in getattr(method, '__matchers__', []):
                decor_func, args, kwargs = decor_params

                method.__skill_attrs__['config'] = self.config
                decorator = decor_func(*args, **kwargs)
                setattr(self, attr, decorator(method))

    @classmethod
    def set_matcher(cls, decor_func, *args, **kwargs):
        def decorator(func):
            add_skill_attributes(func)
            func.__skill_attrs__ = {}

            matchers = getattr(func, '__matchers__', [])
            matchers.append((decor_func, args, kwargs))
            setattr(func, '__matchers__', matchers)

            return func

        return decorator

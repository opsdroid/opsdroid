import logging
from opsdroid.core import OpsDroid

def match_regex(regex):
    def matcher(func):
        for opsdroid in OpsDroid.instances:
            opsdroid.load_regex_skill(regex, func)
        return func
    return matcher

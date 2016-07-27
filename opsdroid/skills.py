""" Decorator functions to use when creating skill modules """

import logging
from opsdroid.core import OpsDroid

def match_regex(regex):
    """ Add decorated function to skills list for regex matching """
    def matcher(func):
        for opsdroid in OpsDroid.instances:
            opsdroid.load_regex_skill(regex, func)
        return func
    return matcher

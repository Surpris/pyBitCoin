#! /usr/bin/python3
# -*- coding: utf-8 -*

import datetime
import functools
# import logging
import os

try:
    from .decorators import dynamic_decorator
    from .get_logger import get_logger
except ImportError:
    import sys
    sys.path.append("../utils/")
    from decorators import dynamic_decorator
    from get_logger import get_logger

_dtformat = "%Y-%m-%d %H:%M:%S"
_dtformat_LOG = "%Y%m%d%H%M%S"

"""setup of logger"""
logdir = "\\".join(os.path.dirname(__file__).split("\\")[:-1]) + "\\log"
if not os.path.exists(logdir):
    os.makedirs(logdir)
_now = datetime.datetime.now()
logpath = os.path.join(logdir, "log_{}.log".format(_now.strftime(_dtformat_LOG)))

logformat = '[%(asctime)s] (%(levelname)s) %(message)s'

_logger = get_logger("debug", logformat, "debug", logpath=logpath)

_loggers = {
    "debug":_logger.debug,
    "info":_logger.info, 
    "warninig":_logger.warning, 
    "error":_logger.error
}

@dynamic_decorator
def footprint(func, loglevel="debug"):
    """footprint(func) -> wrapper function
    Print the datetime when the wrappered function is called, and the name of function.
    """
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        _loggers[loglevel](">> {}()".format(func.__name__))
        func(*args,**kwargs)
        # nowtime = datetime.datetime.now().strftime(_dtformat)
        _loggers[loglevel]("<< {}()".format(func.__name__))
    return wrapper

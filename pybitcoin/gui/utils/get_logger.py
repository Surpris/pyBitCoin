#! /usr/bin/python3
# -*- coding: utf-8 -*

import logging
import os

_loglevels = {
    "debug":logging.DEBUG,
    "info":logging.INFO,
    "warn":logging.WARN,
    "warning":logging.WARNING,
    "critical":logging.CRITICAL,
    "error":logging.ERROR
}

def get_logger(logname, logformat, loglevel, use_file=True, logpath=None, use_stream=True):
    """get_logger(logname, logformat, loglevel, use_file, logpath, use_stream) -> logging.Logger
    make logger

    Parameters
    ----------
    logname : str
    logformat : str
    loglevel : str
    use_file : bool
        if True, log is outputted to the file specified by `logpath`
    logpath : str
        file path to output log
        remarks: this parameter must be assinged if use_file is True
    use_stream : bool
        if True, log is outputted to the stream (console)

    Returns
    -------
    logger : logging.Logger
    """
    logger = logging.getLogger(logname)
    logger.setLevel(_loglevels[loglevel.lower()])
    formatter = logging.Formatter(logformat)

    if use_file:
        if logpath is None or not isinstance(logpath, str):
            raise TypeError("'logpath' must be assigned by a string of path if 'use_file' is True.")
        handler = logging.FileHandler(logpath)
        handler.setFormatter(formatter)
        handler.setLevel(_loglevels[loglevel.lower()])
        logger.addHandler(handler)
        
    if use_stream:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(_loglevels[loglevel.lower()])
        logger.addHandler(handler)
    
    return logger

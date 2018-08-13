#! /usr/bin/python3
# -*- coding: utf-8 -*

import functools

def dynamic_decorator(func0):
    """dynamic_decorator(func0) -> function
    return a dynamic function that the target function can have freedom of arguments

    Parameters
    ----------
    func0 : callable
        function to add a dynamic funciton
    
    Returns
    -------
    wrapper : callable
        wrapper function to have the function
    """
    def wrapper(*args, **kwargs):
        if len(args) != 0 and callable(args[0]):
            # in case where a callable object to the first argument
            func = args[0]
            return functools.wraps(func)(func0(func))
        else:
            # other cases
            def _wrapper(func):
                return functools.wraps(func)(func0(func, *args, **kwargs))
            return _wrapper
    return wrapper

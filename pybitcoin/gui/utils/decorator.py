# -*- coding: utf-8 -*

import functools
import datetime
_dtformat = "%Y-%m-%d %H:%M:%S"

def footprint(func):
    """
    Print the datetime when the wrappered function is called, and the name of function.
    """
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        nowtime = datetime.datetime.now().strftime(_dtformat)
        # if class_name == "":
        print("[{0}] >> {1}()".format(nowtime, func.__name__))
        # else:
        #     print("[{0}] >> {1}.{2}()".format(nowtime, class_name, func.__name__))
        func(*args,**kwargs)
        nowtime = datetime.datetime.now().strftime(_dtformat)
        # if class_name == "":
        print("[{0}] << {1}()".format(nowtime, func.__name__))
        # else:
        #     print("[{0}] << {1}.{2}()".format(nowtime, class_name, func.__name__))
    return wrapper

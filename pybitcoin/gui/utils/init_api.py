#! /usr/bin/python3
# -*- coding: utf-8 -*-

"""
init_api.py
This file offers the following items:

* init_api : function
"""

import glob
import os
import pybitflyer

def init_api(timeout=2.0, verbose=False):
    """init_api(timeout=2.0) -> API
    
    initialize the API of pybitflyer

    Parameters
    ----------
    timeout : float
        timeout of requests
    verbose : bool
        if True, then try requests and print their results

    Returns
    -------
    api : APi instance of pybitflyer
        an API
    """
    _api_timeout = 2.0
    if os.name == "nt":
        fpath = glob.glob(os.path.join(os.environ["USERPROFILE"], ".prv", "*"))[0]
    else:
        fpath = glob.glob(os.path.join(os.environ["HOME"], ".prv", "*"))[0]

    # raise the exception unless both an API key and an API secret key are not loaded.
    with open(fpath, "r", encoding="utf-8") as ff:
        try:
            _api_key = ff.readline().strip()
            _api_secret = ff.readline().strip()
        except Exception as ex:
            raise Exception(ex)

    api = pybitflyer.API(
        api_key=_api_key, 
        api_secret=_api_secret, 
        timeout=_api_timeout
    )

    if verbose:
        try:
            endpoint = "/v1/markets"
            is_success = False
            while not is_success:
                try:
                    currencies = api.request(endpoint)
                    is_success = True
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except:
                    continue
            if isinstance(currencies, list):
                print("Currency:")
                print([currency["product_code"] for currency in currencies])
            else:
                raise ValueError("No available currencies.")

            endpoint = "/v1/me/getpermissions"
            is_success = False
            while not is_success:
                try:
                    permissions = api.request(endpoint)
                    is_success = True
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except:
                    continue
            if isinstance(permissions, list):
                print("Permitted API:")
                print(permissions)
            else:
                print("No permitted APIs.")
        except Exception as ex:
            raise Exception(ex)
    
    return api

if __name__ == "__main__":
    api = init_api(verbose=True)
    print(api)

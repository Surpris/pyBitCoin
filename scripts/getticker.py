#-*- coding: utf-8 -*-

import glob
import os
import pickle
import pybitflyer
import time
from datetime import datetime

_product_code = "FX_BTC_JPY"
_api_dir = ".prv"

# fldrname_for_key = getpass.getpass("folder for key:")
if os.name == "nt":
    fpath = glob.glob(os.path.join(os.environ["USERPROFILE"], _api_dir, "*"))[0]
else:
    fpath = glob.glob(os.path.join(os.environ["HOME"], _api_dir, "*"))[0]

with open(fpath, "r", encoding="utf-8") as ff:
    try:
        _api_key = ff.readline().strip()
        _api_secret = ff.readline().strip()
    except Exception as ex:
        print(ex)

api = pybitflyer.API(api_key=_api_key, api_secret=_api_secret)
try:
    endpoint = "/v1/markets"
    _ = api.request(endpoint)
    print(_)
except Exception as ex:
    raise Exception(ex)

if __name__ == "__main__":
    count = 0
    try:
        while True:
            st = time.time()
            ticker = api.ticker()
            time.sleep(time.time() - st)
    except KeyboardInterrupt:
        print(KeyboardInterrupt)
    
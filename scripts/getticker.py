#! /usr/bin/python3
#-*- coding: utf-8 -*-

import glob
import json
import os
# import pickle
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

fldr = os.path.join(os.path.dirname(__file__), "data")
if not os.path.exists(fldr):
    os.mkdir(fldr)

def save_to_json(fpath, lst):
    result = dict(tickers=tickers)
    with open(fpath, "w") as ff:
        json.dump(result, ff, indent=4)
        print("save to '{}'.".format(fpath))

if __name__ == "__main__":
    count_end = 60
    interval = 1.0
    datetimeFmt = ""
    tickers = []
    start = datetime.now().strftime("%Y%m%d%H%M%S")
    count = 0
    try:
        while True:
            st = time.time()
            ticker = api.ticker(product_code=_product_code)
            tickers.append(ticker)
            count += 1
            print(count)
            if count == count_end:
                end = datetime.now().strftime("%Y%m%d%H%M%S")
                fname = "data_{}_to_{}.json".format(start, end)
                save_to_json(os.path.join(fldr, fname), tickers)
                tickers = []
                start = end
                count = 0
            elapsed = time.time() - st
            if interval > elapsed:
                time.sleep(interval - elapsed)
                
    except KeyboardInterrupt as ex:
        print(ex)
        end = datetime.now().strftime("%Y%m%d%H%M%S")
        fname = "data_{}_to_{}.json".format(start, end)
        save_to_json(os.path.join(fldr, fname), tickers)

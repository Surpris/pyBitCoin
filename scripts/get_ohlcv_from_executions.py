#-*- coding: utf-8 -*-

import copy
from datetime import datetime, timedelta
import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pybitflyer
import time

def initAPI():
    """self.initData() -> None
    initialize the API of pybitflyer.
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

    try:
        endpoint = "/v1/markets"
        currencies = api.request(endpoint)
        if isinstance(currencies, list):
            print("Currency:")
            print([currency["product_code"] for currency in currencies])
        else:
            raise ValueError("No available currencies.")

        endpoint = "/v1/me/getpermissions"
        permissions = api.request(endpoint)
        if isinstance(permissions, list):
            print("Permitted API:")
            print(permissions)
        else:
            print("No permitted APIs.")
    except Exception as ex:
        raise Exception(ex)
    
    return api

def find_id(t, api, guess=None, verbose=False):
    """find_id(t, api, guess=None, verbose=False) -> int
    find an id which comes after and nearest to the datetime 't'.
    
    Parameters
    ----------
    t       : datetime
    api     : API instance of pybitflyer module
    guess   : int
    verbose : bool (default : False)
        if True, then call print functions to inform the current status
    
    Returns
    -------
    id_ : int
    """
    product_code = "FX_BTC_JPY"
    fmt = "%Y-%m-%dT%H:%M:%S.%f"
    fmt2 = "%Y-%m-%dT%H:%M:%S"
    count = 500
    params = {
        "product_code":product_code,
        "count":count
    }
    if guess is not None and isinstance(guess, int):
        params["before"] = guess
    
    id_ = -1
    datetime_ = t.strftime(fmt2)
    while True:
        if verbose:
            print("current id:{}, datetime:{}".format(id_, datetime_))
        results = api.executions(**params)[::-1]
        id_list = np.array([_res["id"] for _res in results])
        
        datetime_list = []
        for _res in results:
            try:
                datetime_list.append(datetime.strptime(_res["exec_date"], fmt))
            except ValueError:
                datetime_list.append(datetime.strptime(_res["exec_date"], fmt2))
        datetime_list = np.array(datetime_list)
        
        index = datetime_list < t
        if index.sum() == 0:
            id_ = 1 * id_list[0]
            params["before"] = id_
            datetime_ = datetime_list[0].strftime(fmt2)
        else:
            id_ = (id_list[index])[-1] + 1
            datetime_ = datetime_list[id_list==id_][0].strftime(fmt2)
            break
    if verbose:
        print("  found id:{}, datetime:{}".format(id_, datetime_))
    
    return id_

def get_ohlcv(ts, te, api, id_start=None, verbose=False):
    """get_ohlcv(ts, te, api, id_start=None, verbose=False) -> numpy.2darray
    
    Parameters
    ----------
    ts       : datetime
        start time in JST
    te       : datetime
        end time in JST
    api      : API inscante of pybitflyer module
    id_start : int (default : None)
        if None, then firstly find the corresponding id.
    verbose  : bool (default : False)
        if True, then call print functions to inform the current status
    
    Returns
    -------
    ohlcv_list : numpy.2darray
        each row has [timestamp, open, high, low, close, volume].
    """
    fmt = "%Y-%m-%dT%H:%M:%S.%f"
    fmt2 = "%Y-%m-%dT%H:%M:%S"
    product_code = "FX_BTC_JPY"
    count = 500
    t_start = ts - timedelta(hours=9)
    t_end = te - timedelta(hours=9)
    
    # processing for id_start
    id_start_ = id_start
    if id_start_ is None:
        if verbose:
            print("find the correspnding id...")
        id_start_ = find_id(t_start, api, False)
        if verbose:
            print("finish. start id: {}".format(id_start_))
    
    # main loop
    t_next = t_start + timedelta(minutes=1)
    ohlcv_list = []
    ltp_list = np.empty(0, dtype=int)
    volume_list = np.empty(0, dtype=int)
    id_next = 1*id_start_
    if verbose:
        print("main loop starts.")
    while t_start <= t_end:
        try:
            if verbose:
                print("start id:{}, datetime:{}".format(id_start_, t_start.strftime("%Y-%m-%dT%H:%M:%S")))
            params = {
                "product_code":product_code,
                "count":count,
                "before":id_next + count + 1,
            }
            ## get executions
            is_success = False
            fault_count = 0
            while not is_success:
                try:
                    results = api.executions(**params)[::-1]
                    is_success = True
                except KeyboardInterrupt:
                    return pd.DataFrame(ohlcv_list, columns=["time", "id_start", "open", "high", "low", "close", "volume"])
                except:
                    fault_count += 1
                    continue

            ## extract
            ids_ = np.array([_res["id"] for _res in results], dtype=int)
            ltps_ = np.array([_res["price"] for _res in results], dtype=int)
            volumes_ = np.array([_res["size"] for _res in results], dtype=int)
            datetimes_ = []
            for _res in results:
                try:
                    datetimes_.append(datetime.strptime(_res["exec_date"], fmt))
                except ValueError:
                    datetimes_.append(datetime.strptime(_res["exec_date"], fmt2))
            datetimes_ = np.array(datetimes_)
            
            ## find valid indices & extract
            ind_id = ids_ >= id_next
            ind_now = (datetimes_ >= t_start) & (datetimes_ < t_next)
            ind_next = datetimes_ >= t_next
            ltp_list = np.hstack((ltp_list, ltps_[ind_id&ind_now]))
            volume_list = np.hstack((volume_list, volumes_[ind_id&ind_now]))
            
            ## processing for next step
            # if (ind_id&ind_now).sum() == 0:
            #     id_start_ = 
            #     continue
            if ind_next.sum() == 0:
                id_next = 1*(ids_[ind_id&ind_now])[-1]
            else:
                timestamp_ = t_start.timestamp()
                ohlcv_list.append([timestamp_, id_start_, ltp_list[0], ltp_list.max(), ltp_list.min(), ltp_list[-1], volume_list.sum()])
                id_start_ = 1*(ids_[ind_id&ind_next])[0]
                id_next = 1*(ids_[ind_id&ind_next])[-1]
                ltp_list = np.empty(0, dtype=int)
                ltp_list = np.hstack((ltp_list, ltps_[ind_id&ind_next]))
                volume_list = np.empty(0, dtype=int)
                volume_list = np.hstack((volume_list, volumes_[ind_id&ind_next]))
                t_start += timedelta(minutes=1)
                t_next += timedelta(minutes=1)
                print("next id:{}, datetime:{}".format(id_start_, t_start.strftime("%Y-%m-%dT%H:%M:%S")))
        except KeyboardInterrupt:
            return pd.DataFrame(ohlcv_list, columns=["time", "id_start", "open", "high", "low", "close", "volume"])
    if verbose:
            print("finish the main loop.")
    return pd.DataFrame(ohlcv_list, columns=["time", "id_start", "open", "high", "low", "close", "volume"])

if __name__ == "__main__":
    api = initAPI()
    # id_start = 694426164 # 2019/01/01
    # id_start = 707791510 # 2019/01/07
    # id_start = 710557268 # 2019/01/08
    # id_start = 713238915 # 2019/01/09
    # id_start = 715822823 # 2019/01/10
    # id_start = 718327164 # 2019/01/11
    # id_start = 721123808 #  2019/01/12
    id_start = 723565551 # 2019/01/13
    t_start = datetime(2019, 1, 13, 0, 1, 0)
    t_end = datetime(2019, 1, 14, 0, 0, 0)
    st = time.time()
    ohlcv = get_ohlcv(t_start, t_end, api, id_start, verbose=False)
    t_last = datetime.fromtimestamp(ohlcv["time"].values[-1]) + timedelta(hours=9)
    print("Elapsed time:{0:.2f} sec".format(time.time()-st))

    ohlcv.to_csv("../data/ohlcv/OHLCV_{}_to_{}.csv".\
                format(t_start.strftime("%Y%m%d%H%M"), t_last.strftime("%Y%m%d%H%M")))
    ohlcv.to_csv("../pybitcoin/gui/data/ohlcv/OHLCV_{}_to_{}.csv".\
                format(t_start.strftime("%Y%m%d%H%M"), t_last.strftime("%Y%m%d%H%M")))
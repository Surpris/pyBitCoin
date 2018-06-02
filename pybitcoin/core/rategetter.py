#-*- coding: utf-8 -*-

import urllib.request
import urllib.parse
import json
import numpy as np
import pandas as pd
import copy
import datetime

def getRateViaCrypto(histoticks, params):
    """getRateViaCrypto(histoticks, params) -> 
    get rate via CryptoCompare (https://min-api.cryptocompare.com/).
    params should be a dict object with items of str.
    <params>
    histoticks: day, hour, minute or some tick (see the site)
    params: parameters to send the site 
        fsym : currency symbol of interest (required)
        tsym : currency symbol to convert into (required)
        limit: limit of retrieved data (max: 2000)
        e    : the exchange to obtain data from (CCCAGG - by default)
        toTs : last unix timestamp to return data for
    </params>
    
    <return>
    retrieved data (json object)
    </return>
    """
    
    url = "https://min-api.cryptocompare.com/data/"
    url += "histo{}".format(histoticks) + "?" + urllib.parse.urlencode(params) 
    res = urllib.request.urlopen(url)
    result = json.loads(res.read().decode('utf-8'))
    return result

datetimeFmt = "%Y-%m-%dT%H:%M:%S.%f"

def toDataFrame(data, is_datetime=False):
    """toDataFrame(data)
    convert data to a DataFrame object.
    'data' is obtained from CryptoCompare.
    The values in the 'time' are converted to datetime strings 
    if 'is_datetime' == True.
    
    <params>
    data       : data obtained from CryptoCompare (dict object)
    is_datetime: boolean
    </params>
    
    <return>
    a DataFrame object
    </return>
    """
    
    if not isinstance(data, dict):
        raise TypeError
    keys = data["Data"][0].keys()
    
    output = np.zeros((len(data["Data"]), len(keys)), dtype=object)
    for ii, col in enumerate(data["Data"]):
        if is_datetime:
            buff = copy.deepcopy(col)
            datetime1 = datetime.datetime.fromtimestamp(buff["time"])
            buff["time"] = datetime1.strftime(datetimeFmt)
            output[ii] = np.array([buff[key] for key in keys], dtype=object)
        else:
            output[ii] = np.array([col[key] for key in keys])
        
    return pd.DataFrame(output, columns=list(keys))
    
def toCSV(data, fpath, is_datetime=False):
    """toCSV(data, fpath)
    save data to a csv file with the path of 'fpath'.
    'data' must have datasets specified by the 'Data' key.
    The values in the 'time' are converted to datetime strings 
    if 'is_datetime' == True.
    
    <params>
    data       : data obtained from CryptoCompare (dict object)
    fpath      : full (or relative) path to save data to
    is_datetime: boolean
    </params>
    
    <return>
    None
    </return>
    """
    df = toDataFrame(data)
    df.to_csv(fpath)

if __name__ == "__main__":
    histoticks = "hour"
    params = {
        "fsym": "BTC",
        "tsym": "JPY",
        "limit": "5",
        "e": "bitFlyer"
    }
    result = getRateViaCrypto(histoticks, params)
    print(toDataFrame(result, False))
    toCSV(result, "./test.csv")

if __name__ == "__main__":
    histoticks = "hour"
    params = {
        "fsym": "BTC",
        "tsym": "JPY",
        "limit": "24",
        "e": "bitFlyer"
    }
    result = getRateViaCrypto(histoticks, params)
    for key in result.keys():
        if key != "Data":
            print(key, result[key])
        else:
            print(key)
            for data in result[key]:
                print(data)
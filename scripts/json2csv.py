#! /usr/bin/python3
#-*- coding: utf-8 -*-
"""json2csv.py
This script aims to compile json files made by 'getticker.py' 
to a csv file via pandas.DataFrame.
Each json file has a format of name, 'data_%Y%m%d%H%M%S_to_%Y%m%d%H%M%S.json'.

This script requires the followng parameters:

Parameters
----------
fldr : str
    path of folder which containes files to compile
file_count : int
    # of files from the first file to compile
remove_file : bool
    whether to remove files which contain the compiled data

Returns
-------
A file with the extension of 'csv' which contains all the compiled data
"""

import glob
import json
import numpy as np
import os
import pandas as pd
import sys

def main(fldr, file_count, remove_files):
    if file_count == "all":
        main_to_all(fldr, remove_files)
        return
    file_count = int(file_count)
    print("compilatioin starts...")
    filelist_ = glob.glob(os.path.join(fldr, "*.json"))
    if len(filelist_) == 0:
        print("warning: No json files are found.\nexit.")
        sys.exit(-1)
    if len(filelist_) < file_count:
        print("# of json files are smaller than the given number of files.\nexit.")
        sys.exit(-1)
    
    filelist = filelist_[:file_count]
    date_start = os.path.splitext(filelist[0])[0].split("_")[-3]
    if file_count == 1:
        date_end = os.path.splitext(filelist[0])[0].split("_")[-1]
    else:
        date_end = os.path.splitext(filelist[-1])[0].split("_")[-1]
    output_path = os.path.join(fldr, "data_{}_to_{}.csv".format(date_start, date_end))
    df = None
    header = None
    ary = []
    for fpath in filelist:
        print(fpath)
        with open(fpath, "r") as ff:
            tickers = json.load(ff)["tickers"]
        if len(tickers) == 0:
            continue
        if not isinstance(tickers, list):
            print("Unexpected format:{}. 'tickers' must have a type of list.".format(type(tickers)))
        if header is None:
            header = list(tickers[0].keys())
        for ticker in tickers:
            lst = []
            for key in header:
                lst.append(ticker[key])
            ary.append(lst)
    ary = np.array(ary)
    df = pd.DataFrame(ary, columns=header)
    print("compilation was finished.")
    df.to_csv(output_path)
    print("save to {}".format(output_path))

    if remove_files == "True":
        print("remove the original files...")
        for fpath in filelist:
            os.remove(fpath)

def main_to_all(fldr, remove_files):
    print("conversion starts...")
    filelist = glob.glob(os.path.join(fldr, "*.json"))
    for fpath in filelist:
        print(fpath)
        date_start = os.path.splitext(fpath)[0].split("_")[-3]
        date_end = os.path.splitext(fpath)[0].split("_")[-1]
        output_path = os.path.join(fldr, "data_{}_to_{}.csv".format(date_start, date_end))

        df = None
        header = None
        ary = []
        with open(fpath, "r") as ff:
            tickers = json.load(ff)["tickers"]
        if len(tickers) == 0:
            continue
        if not isinstance(tickers, list):
            print("Unexpected format:{}. 'tickers' must have a type of list.".format(type(tickers)))
        if header is None:
            header = list(tickers[0].keys())
        try:
            for ticker in tickers:
                lst = []
                for key in header:
                    lst.append(ticker[key])
                ary.append(lst)
            ary = np.array(ary)
            df = pd.DataFrame(ary, columns=header)
            df.to_csv(output_path)
        except Exception as ex:
            print(ex)
    print("conversion was finished.")
    if remove_files == "True":
        print("remove the original files...")
        for fpath in filelist:
            os.remove(fpath)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

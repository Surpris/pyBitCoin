#-*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from .mathfunctions import calc_EMA, find_cross_points, peakdet, symbolize

def analyze(df, N1, N2, N_dec=5, patterns_golden=None, patterns_dead=None):
    """analyze(df, N1, N2, N_dec=5, patterns_golden=None, patterns_dead=None) -> dict
    calculate some factors
    
    Parameters
    ----------
    df              : pandas.DataFrame
    N1              : int
    N2              : int
    N_dec           : int
    patterns_golden : array-like
    patterns_dead   : array-like
    
    Returns
    -------
    results : dict
    """
    close_ = df["close"].values
    open_ = df["open"].values
    
    # calcualte EMA
    ema1 = calc_EMA(close_, N1)
    ema2 = calc_EMA(close_, N2)
    
    # find cross points
    cross_points = find_cross_points(ema1, ema2)
    ind_ = cross_points != 0
    a_k = np.vstack((np.arange(len(cross_points))[ind_], cross_points[ind_])).transpose().astype(int)
    
    # find local maxima and minima of the difference, "EMA1 - EMA2"
    ema_diff = ema1 - ema2
    maxtab_ema_diff, mintab_ema_diff = peakdet(ema_diff, 10)
    
    # symbolize
    dec = symbolize(df, N_dec)
    
    # extract factors for each godlen/dead cross points
    dec_ext = np.zeros(len(a_k), int)
    t1_ext = np.zeros(len(a_k), int)
    tm_ext = np.zeros(len(a_k), int)
    distance_ext = np.zeros(len(a_k), int)
    
    for ii in range(len(a_k)-1):
        ind1, ind2 = a_k[ii][0], a_k[ii+1][0]
        
        v = a_k[ii][1]
        o_ = open_[ind1:ind2]
        c_ = close_[ind1:ind2]
        if v < 0: # dead cross
            if patterns_dead is None or dec[ind1] in patterns_dead:
                # start value
                if len(o_) > 1:
                    t1_ext[ii] = min(o_[1], c_[1])
                else:
                    t1_ext[ii] = min(o_[0], c_[0])

                # minimum index
                index = (mintab_ema_diff[:, 0]>=ind1)&(mintab_ema_diff[:, 0]<ind2)
                count = index.sum()
                if count > 0:
                    tm = (mintab_ema_diff[index, 0]).astype(int)[0]
                else:
                    tm = ind1
                tm_ext[ii] = max(open_[tm+1], close_[tm+1])
                distance_ext[ii] = tm - ind1 + 1
                dec_ext[ii] = dec[ind1]
        else: # golden cross
            if patterns_golden is None or dec[ind1] in patterns_golden:
                # start value
                if len(o_) > 1:
                    t1_ext[ii] = max(o_[1], c_[1])
                else:
                    t1_ext[ii] = max(o_[0], c_[0])

                # maximum index
                index = (maxtab_ema_diff[:, 0]>=ind1)&(maxtab_ema_diff[:, 0]<ind2)
                count = index.sum()
                if count > 0:
                    tm = (maxtab_ema_diff[index, 0]).astype(int)[0]
                else:
                    tm = ind1
                tm_ext[ii] = min(open_[tm+1], close_[tm+1])
                distance_ext[ii] = tm - ind1 + 1
                dec_ext[ii] = dec[ind1]
    
    # calculate benefits
    benefits = tm_ext - t1_ext
    benefits[np.abs(benefits)>1e5] = 0.0
    
    # extract statistics and value-pattern pairs
    stat_dead = np.zeros((2**N_dec , 5), float) # max, min, mean, std, median
    list_ext_dead = [np.empty(0, dtype=float)] * 2**N_dec
    for ii, ind in enumerate(dec_ext[a_k[:, 1] == -1]):
        v = benefits[a_k[:, 1] == -1][ii]
        list_ext_dead[ind] = np.append(list_ext_dead[ind], v)

    for ii in range(len(list_ext_dead)):
        arr = list_ext_dead[ii]
        if len(arr) != 0:
            ind = np.abs(arr) <=100000
            list_ext_dead[ii] = arr[ind]
            stat_dead[ii] = np.array([arr[ind].max(), arr[ind].min(), arr[ind].mean(), arr[ind].std(), np.median(arr[ind])])

    stat_golden = np.zeros((2**N_dec , 5), float) # max, min, mean, std, median
    list_ext_golden = [np.empty(0, dtype=float)] * 2**N_dec
    for ii, ind in enumerate(dec_ext[a_k[:, 1] == 1]):
        v = benefits[a_k[:, 1] == 1][ii]
        list_ext_golden[ind] = np.append(list_ext_golden[ind], v)

    for ii in range(len(list_ext_golden)):
        arr = list_ext_golden[ii]
        if len(arr) != 0:
            ind = np.abs(arr) <=100000
            list_ext_golden[ii] = arr[ind]
            stat_golden[ii] = np.array([arr[ind].max(), arr[ind].min(), arr[ind].mean(), arr[ind].std(), np.median(arr[ind])])
    
    results = dict(
        ema1=ema1, ema2=ema2, cross_points=cross_points, a_k=a_k,
        dec_ext=dec_ext, distance_ext=distance_ext, benefits=benefits,
        stat_dead=stat_dead, list_ext_dead=list_ext_dead,
        stat_golden=stat_golden, list_ext_golden=list_ext_golden
    )
    return results

def main(N1, N2, N_dec):
    """main(N1, N2, N_dec) -> None
    execute analyze() and draw the results
    """
    # import matplorlib.pyplot as plt
    import glob
    file_list = glob.glob("../data/ohlcv/OHLCV*.csv")
    data = None
    for fpath in file_list:
        print(fpath)
        if data is None:
            data = pd.read_csv(fpath, index_col=0)
        else:
            data = pd.concat((data, pd.read_csv(fpath, index_col=0)))
    results = analyze(data, N1, N2, N_dec)
    # plt.show()
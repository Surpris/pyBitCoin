#! /usr/bin/python3
# -*- coding: utf-8 -*-

import numpy as np
from scipy.signal import lfilter
import sys

def calc_EMA(x, N):
    """calc_EMA(x, N) -> array-like
    calculate exponential moving average (EMA)
    """
    return _calc_EMA(x, 2./(N + 1.))

def _calc_EMA(x, alpha):
    """ _calc_EMA(x, alpha) -> array-like
    Adopted from https://qiita.com/toyolab/items/6872b32d9fa1763345d8
    """
    y,_ = lfilter([alpha], [1,alpha-1], x, zi=[x[0]*(1-alpha)])
    return y

def find_cross_points(y1, y2=None):
    """find_cross_points(y1, y2=None) -> numpy.1darray
    find cross points between two data sequences
    If y2 == None, then find the root of y1.
    
    Parameters
    ----------
    y1 : list or numpy.1darray
    y2 : list or numpy.1darray
    
    Returns
    -------
    cross_points : numpy.1darray
    """
    if y2 is None:
        y2 = np.zeros_like(y1)
    if isinstance(y1, list):
        y1 = np.array(y1)
    if isinstance(y2, list):
        y2 = np.array(y2)
    cross_points = np.zeros(len(y1))
    for ii in range(1, len(y1)):
        if y1[ii - 1] >= y2[ii - 1] and y1[ii] < y2[ii]:
            cross_points[ii] = -1
        elif y1[ii - 1] < y2[ii - 1] and y1[ii] >= y2[ii]:
            cross_points[ii] = 1
    return cross_points

def symbolize(dataFrame, k):
    """symbolize(dataFrame, k) -> numpy.1darray
    binalize a k-length OHLC dataset and then convert the binary to decimal number.  
    
    Parameters
    ----------
    dataFrame : pandas.DataFrame
    k : int
    
    Returns
    -------
    dec : numpy.1darray
    """
    if k <= 0:
        raise ValueError("k must be >=1.")
    try:
        var_ = (dataFrame["Close"] - dataFrame["Open"]).values
    except KeyError:
        var_ = (dataFrame["close"] - dataFrame["open"]).values
    dec = np.zeros(len(var_), int)
    
    for ii in range(k-1, len(var_)):
        ind_ = np.array(var_[ii-k+1:ii+1] >= 0, int)
        dec[ii] = int("".join([str(i_) for i_ in ind_]), 2)
    return dec

def peakdet(v, delta, x=None):
    """peakdet(v, delta, x=None) -> numpy.2darray, numpy.2darray
    Converted from MATLAB script at http://billauer.co.il/peakdet.html
    returns two arrays which include the local maxima and the local minima.
    function [maxtab, mintab]=peakdet(v, delta, x)
    % PEAKDET Detect peaks in a vector
    % [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    % maxima and minima ("peaks") in the vector V.
    % MAXTAB and MINTAB consists of two columns. Column 1
    % contains indices in V, and column 2 the found values.
    %
    % With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    % in MAXTAB and MINTAB are replaced with the corresponding
    % X-values.
    %
    % A point is considered a maximum peak if it has the maximal
    % value, and was preceded (to the left) by a value lower by
    % DELTA.
    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.
    
    Parameters
    ----------
    v     : array-like
    delta : numeric
    x     : array-like (default : None)
    
    Returns
    -------
    maxtab : numpy.2darray
    mintab : numpy.2darray
    """
    maxtab = []
    mintab = []
    if x is None:
        x = np.arange(len(v))
        v = np.asarray(v)
    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')
    if not np.isscalar(delta):
        sys.exit('Input argument delta must be a scalar')
    if delta <= 0:
        sys.exit('Input argument delta must be positive')
    mn, mx = np.Inf, -np.Inf
    mnpos, mxpos = np.NaN, np.NaN
    lookformax = True

    for i in np.arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
        if lookformax:
            if this < mx - delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn + delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return np.array(maxtab), np.array(mintab)

def dataset_for_boxplot(arr, k=0):
    """dataset_for_boxplot(arr, k=0) -> tuple
    
    return a tuple having the folloing elements:
        timestamp      : int
            timestamp
        outliers       : array-like
            outliers
        lower whisker  : float
            lower whisker
        first quartile : float
            first quartile
        median         : float
            median
        third quartile : float
            third quartile 
        upper whisker  : float
            upper whisker

    Parameters
    ----------
    arr : array-like
        list of values
    k   : numeric
        equivalent to timestamp
    
    Returns
    -------
    a tuple having the above format
    """
    if len(arr) == 0:
        return (k, [], 0, 0, 0, 0, 0)
    if not isinstance(arr, np.ndarray):
        arr = np.array(arr)
    q1 = np.percentile(arr, 25)
    q2 = np.median(arr)
    q3 = np.percentile(arr, 75)
    IQR = q3 - q1
    ind = (arr >= q1 - 1.5 * IQR) & (arr <= q3 + 1.5 * IQR)
    outliers = arr[~ind]
    lower_whisker = arr[ind].min()
    upper_whisker = arr[ind].max()
    return (k, outliers, lower_whisker, q1, q2, q3, upper_whisker)
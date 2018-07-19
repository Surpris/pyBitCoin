#! /usr/bin/python3
# -*- coding: utf-8 -*-
from scipy.signal import lfilter

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
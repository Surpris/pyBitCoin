# -*- coding: utf-8 -*-
from scipy.signal import lfilter

def calc_EMA(x, alpha):
    """ calc_EMA(x, alpha)
    Adopted from https://qiita.com/toyolab/items/6872b32d9fa1763345d8
    """
    y,_ = lfilter([alpha], [1,alpha-1], x, zi=[x[0]*(1-alpha)])
    return y
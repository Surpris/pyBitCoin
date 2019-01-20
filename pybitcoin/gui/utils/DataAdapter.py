#! /usr/bin/python3
# -*- coding: utf-8 -*-

import copy
import datetime
import numpy as np
import pandas as pd
import pickle
# import sys
# import pybitflyer
from .footprint import footprint
from .mathfunctions import symbolize

class DataAdapter(object):
    """DataAdapter(object)
    This class offers an adapter of a dataset to be used in pybitcoin.
    """
    def __init__(self, df=None, analysis_results=None, 
                 N_ema_min=10, N_ema_max=30, N_ema1=20, N_ema2=21, 
                 delta=10., N_dec=5):
        """__init__(self, df=None, analysis_results=None, 
                    N_ema_min=10, N_ema_max=30, N_ema1=20, N_ema2=21, 
                    delta=10., N_dec=5) -> None
        initialize this class

        Parameters
        ----------
        df               : pandas.DataFrame (default : None)
            OHLCV dataset
        analysis_results : dict (default : None)
            results of analysis
        N_ema_min        : int (default : 10)
            the minimum of N number for EMA lines
        N_ema_max        : int (default : 30)
            the maximum of N number for EMA lines
        N_ema1           : int (default : 20)
            N number for the first EMA line
        N_ema2           : int (default : 21)
            N number for the second EMA line
        delta            : float (default : 10.0)
            threshold for the extreme points
        N_dec            : int (default : 5)
            the exponent of the decimal for OHLC patterns
        """
        self._data_frame = df
        self._analysis_results = analysis_results

        # for OHLCV
        self.N_ema_min = N_ema_min
        self.N_ema_max = N_ema_max
        self._N_ema1 = N_ema1
        self._N_ema2 = N_ema2
        self.delta = delta # for judgement of extreme maxima / minima
        self.N_dec = N_dec

        # initialize inner data
        self._df_initialized = True
        self._ema_updated = True
        self.updateAlpha()
        self.initOHLCVData()

        self._ana_initialized = True
        self._ana_updated = True
        self.initAnalysisData()
    
    @footprint
    def initOHLCVData(self):
        """initInnerData(self) -> None
        initialize the inner data for OHLCV
        """
        if not hasattr(self, "_tmp_target"):
            self._tmp_target = [
                "N_ema1", "N_ema2", "ltp", "timestamp", "ohlc_list", "volume_list", "close", 
                "ema1", "ema2", "cross_signal", "extreme_signal", 
                "current_max", "current_min", "look_for_max", "jpy_list", "benefit_list", 
                "current_state", "order_ltp", "stop_by_cross", 
            ]
        self._latest = None
        self._tmp_ltp = []
        self._tmp_ohlc = []
        if self._df_initialized:
            self._ltp = []
            self._timestamp = []
            self._ohlc_list = []
            self._volume_list = []
            self._dec = None
            self._ema_updated = True
        if self._ema_updated:
            self._close = []
            self._ema1 = []
            self._ema2 = []
            self._cross_signal = []
            self._extreme_signal = []
            self._current_max = np.Inf
            self._current_min = -np.Inf
            self._look_for_max = None
            self._jpy_list = []
            self._benefit_list = []
            self._current_state = "wait"
            self._order_ltp = 0
            self._stop_by_cross = False

        if self._data_frame is not None:
            if isinstance(self._data_frame, pd.DataFrame):
                data_ = self._data_frame[["open", "high", "low", "close"]].values
                volume_ = self._data_frame["volume"].values
                for ii, row in enumerate(data_):
                    buff = np.zeros(5)
                    buff[0] = ii + 1
                    buff[1:] = row.copy()
                    if self._df_initialized:
                        self._timestamp.append(ii + 1)
                        self._volume_list.append(volume_[ii])
                        self._ohlc_list.append(buff.copy())
                    if self._ema_updated:
                        self._close.append(row[-1])
                        self._ema1.append(self.calcEMA(self._ema1, self._alpha1))
                        self._ema2.append(self.calcEMA(self._ema2, self._alpha2))
                        self._cross_signal.append(self.judgeCrossPoint())
                        self._extreme_signal.append(self.judgeExtremePoint())
                        self.updateExecutionState()
                if self._df_initialized:
                    self._dec = symbolize(self._data_frame, self.N_dec)
            else:
                raise TypeError('df must be a pandas.DataFrame object.')
        self._df_initialized = False
        self._ema_updated = False
    
    def calcEMA(self, ema_list, alpha):
        """calcEMA(self, ema_list, alpha) -> float
        calculate the EMA value for the latest close data

        Parameters
        ----------
        ema_list : array-like
            list of historical EMA values
        alpha : float
            alpha parameter of EMA calculation
        
        Returns
        -------
        current EMA value (float)
        """
        if len(ema_list) == 0:
            return self._close[-1]
        else:
            return (1. - alpha) * ema_list[-1] + alpha * self._close[-1]
    
    def judgeCrossPoint(self):
        """judgeCrossPoint(self) -> float
        judge whether one is on a cross point

        Returns
        -------
        judgement value (float)
            +1.0 : on a golden cross point
             0.0 : not on any cross point
            -1.0 : on a dead cross point
        """
        if len(self._ema1) == 0 or len(self._ema2) == 0:
            raise ValueError("Some error occurs on the inner data.")
        if len(self._ema1) == 1 or len(self._ema2) == 1:
            return 0.
        
        ema1_before, ema1_current = self._ema1[-2], self._ema1[-1]
        ema2_before, ema2_current = self._ema2[-2], self._ema2[-1]
        if ema1_before >= ema2_before and ema1_current < ema2_current:
            return -1.
        elif ema1_before < ema2_before and ema1_current >= ema2_current:
            return 1.
        else:
            return 0.
        
    def judgeExtremePoint(self):
        """judgeExtremePoint(self) -> float
        judge whether one is on an extreme point

        Returns
        -------
        judgement value (float)
            +1.0 : on an extreme maximum
             0.0 : not on any extreme maximum or minumum
            -1.0 : on an extreme minimum
        """
        if len(self._ema1) == 0 or len(self._ema2) == 0:
            raise ValueError("Some error occurs on the inner data.")
        if self._look_for_max is None:
            return 0.
        diff = self._ema1[-1] - self._ema2[-1]
        self._current_max = max([diff, self._current_max])
        self._current_min = min([diff, self._current_min])
        if self._look_for_max and diff < self._current_max - self.delta:
            self._look_for_max = False
            self._current_min = diff
            return 1.
        elif (not self._look_for_max) and diff > self._current_min + self.delta:
            self._look_for_max = True
            self._current_max = diff
            return -1.
        else:
            return 0.
    
    def updateExecutionState(self):
        """updateExecutionState(self) -> None
        update the state of execution
        #TODO: modify this method
        """
        if len(self._close) == 1:
            self._jpy_list.append(0)
            self._benefit_list.append(0)
            return
        self._jpy_list.append(self._jpy_list[-1])
        self._benefit_list.append(0)
        if self._current_state == "ask":
            if self._stop_by_cross: # when the previous state is "buy"
                ltp_ = max([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])
                self._jpy_list[-1] -= ltp_ - self._order_ltp
                self._benefit_list[-1] -= ltp_ - self._order_ltp
            self._order_ltp = max([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])    
            self._current_state = "sell"
        elif self._current_state == "bid":
            if self._stop_by_cross: # when the previous state is "sell"
                ltp_ = min([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])
                self._jpy_list[-1] += ltp_ - self._order_ltp
                self._benefit_list[-1] += ltp_ - self._order_ltp
            self._order_ltp = min([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])
            self._current_state = "buy"
        elif self._current_state == "sell":
            if self._extreme_signal[-2] == 1.:
                ltp_ = min([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])
                self._jpy_list[-1] += ltp_ - self._order_ltp
                self._benefit_list[-1] += ltp_ - self._order_ltp
                self._order_ltp = 0
                self._current_state = "wait"
                self._look_for_max = None
        elif self._current_state == "buy":
            if self._extreme_signal[-2] == -1.:
                ltp_ = max([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])
                self._jpy_list[-1] -= ltp_ - self._order_ltp
                self._benefit_list[-1] -= ltp_ - self._order_ltp
                self._order_ltp = 0
                self._current_state = "wait"
                self._look_for_max = None
        if self._cross_signal[-1] == 1.: # ask in the next step
            if self._current_state == "buy":
                self._stop_by_cross == True
            self._look_for_max = True
            self._current_state = "ask"
        elif self._cross_signal[-1] == -1.: # bid in the next step
            if self._current_state == "sell":
                self._stop_by_cross == True
            self._look_for_max = False
            self._current_state = "bid"
    
    @footprint
    def initAnalysisData(self):
        """initAnalysisData(self) -> None
        initialize the inner data for analysis
        """
        if self._ana_initialized or self._ana_updated:
            self._benefit_map = np.zeros((self.N_ema_max + 1, self.N_ema_max + 1), dtype=int)
            # self._results_list = []
            self._stat_dead_list = []
            self._stat_golden_list = []
            self._dec_dead_list = []
            self._dec_golden_list = []
            # if self._ana_initialized and self._analysis_results is not None:
            #     if isinstance(self._analysis_results, dict):
            #         self._benefit_map = self._analysis_results.get("benefit_map", self._benefit_map)
            #         self._results_list = self._analysis_results.get("results_list", [])
            #     else:
            #         raise TypeError('analysis_results must be a dict object.')
            if self._ana_updated:
                # reserve the current dataset temporaly
                for s in self._tmp_target:
                    exec("tmp_{0} = copy.deepcopy(self._{0})".format(s))
                
                # calculate statistics and benefits for each pair (N_ema1, N_ema2)
                for ii in range(self.N_ema_min, self.N_ema_max):
                    # calculate a dataset of signals
                    self._N_ema1 = ii
                    self._N_ema2 = ii + 1
                    self.updateAlpha()
                    self.initOHLCVData()
                    self._benefit_map[ii, ii + 1] = 1*self._jpy_list[-1]

                    # extract patterns
                    dec_dead = [np.empty(0)] * 2**self.N_dec
                    dec_golden = [np.empty(0)] * 2**self.N_dec
                    for jj in range(len(self._cross_signal)):
                        print(jj)
                        if self._cross_signal[jj] == 1: # golden case
                            buff = self._benefit_list[jj:]
                            buff2 = np.array(self._extreme_signal[jj:], dtype=float)
                            v = buff[np.where(buff2 == 1.)[0][0] + 1]
                            dec_golden[self._dec[jj]] = \
                                np.append(dec_golden[self._dec[jj]], v)
                        elif self._cross_signal[jj] == -1: # dead case
                            buff = self._benefit_list[jj:]
                            buff2 = np.array(self._extreme_signal[jj:], dtype=float)
                            v = buff[np.where(buff2 == -1.)[0][0] + 1]
                            dec_dead[self._dec[jj]] = \
                                np.append(dec_dead[self._dec[jj]], v)
                    
                    # calculate statistics
                    stat_dead = np.zeros((2**self.N_dec, 5), dtype=float)
                    stat_golden = np.zeros((2**self.N_dec, 5), dtype=float)
                    for jj in range(2**self.N_dec):
                        # golden case
                        arr = dec_golden[jj]
                        if len(arr) != 0:
                            ind = np.abs(arr) <=100000
                            dec_golden[ii] = arr[ind]
                            stat_golden[ii] = np.array([
                                arr[ind].max(), 
                                arr[ind].min(), 
                                arr[ind].mean(), 
                                arr[ind].std(), 
                                np.median(arr[ind])
                            ])
                        # dead case
                        arr = dec_dead[ii]
                        if len(arr) != 0:
                            ind = np.abs(arr) <=100000
                            dec_dead[ii] = arr[ind]
                            stat_dead[ii] = np.array([
                                arr[ind].max(), 
                                arr[ind].min(), 
                                arr[ind].mean(), 
                                arr[ind].std(), 
                                np.median(arr[ind])
                            ])
                        
                    # append
                    self._dec_golden_list.append(dec_golden)
                    self._dec_dead_list.append(dec_dead)
                    self._stat_golden_list.append(stat_golden)
                    self._stat_dead_list.append(stat_dead)
                    break
                
                # set the preserved dataset to the inner parameters
                for s in self._tmp_target:
                    exec("self._{0} = copy.deepcopy(tmp_{0})".format(s))
                self.updateAlpha()
            self._ana_initialized = False
            self._ana_updated = False
    
    def updateAlpha(self):
        """updateAlpha(self) -> None
        update the alpha parameters for calulation of EMA
        """
        self._alpha1 = 2./(self._N_ema1 + 1.)
        self._alpha2 = 2./(self._N_ema2 + 1.)
    
    @footprint
    def save(self, fpath):
        """save(self, fpath) -> None
        save this instance

        Parameters
        ----------
        fpath : str
            file path to save
        """
        with open(fpath, "wb") as ff:
            pickle.dump(self, ff)
        
    def load(fpath):
        """load(fpath) -> self
        load one instance of this class from fpath

        Parameters
        ----------
        fpath : str
            file path to load
        """
        with open(fpath, "rb") as ff:
            obj = pickle.load(ff)
        return obj
    
    @property
    def data(self):
        return self._data_frame
    
    @data.setter
    def data(self, df):
        self._data_frame = df
        self._df_initialized = True
        self.initOHLCVData()
    
    @property
    def analysis_results(self):
        return self._analysis_results
    
    @analysis_results.setter
    def analysis_results(self, data):
        self._analysis_results = data
        self._ana_initialized = True
        self.initAnalysisData()
    
    @property
    def N_ema1(self):
        return self._N_ema1
    
    @N_ema1.setter
    def N_ema1(self, N):
        self._N_ema1 = N
        self._alpha1 = 2./(self._N_ema1 + 1.)
        self._ema_updated = True
    
    @property
    def N_ema2(self):
        return self._N_ema2
    
    @N_ema2.setter
    def N_ema2(self, N):
        self._N_ema2 = N
        self._alpha2 = 2./(self._N_ema2 + 1.)
        self._ema_updated = True

    @property
    def timestamp(self):
        return self._timestamp
    
    @property
    def latest_ltp(self):
        return self._latest
    
    @property
    def ohlc_list(self):
        return self._ohlc_list
    
    @property
    def volume_list(self):
        return self._volume_list
    
    @property
    def close_list(self):
        return self._close
    
    @property
    def ema1(self):
        return self._ema1
    
    @property
    def ema2(self):
        return self._ema2
    
    @property
    def cross_signal(self):
        return self._cross_signal
    
    @property
    def extreme_signal(self):
        return self._extreme_signal
    
    @property
    def jpy_list(self):
        return self._jpy_list
    
    @property
    def current_state(self):
        return self._current_state
    
    @property
    def order_ltp(self):
        return self._order_ltp
#! /usr/bin/python3
# -*- coding: utf-8 -*-

"""
DataAdapter.py
This file offers the following items:

* DataAdapter
"""

import copy
from datetime import datetime, timedelta
from itertools import combinations
import numpy as np
import pandas as pd
import pickle
import sys
import pybitflyer

try:
    from .footprint import footprint
    from .init_api import init_api
    from .mathfunctions import symbolize, dataset_for_boxplot
except ImportError:
    sys.path.append("../utils/")
    from footprint import footprint
    from init_api import init_api
    from mathfunctions import symbolize, dataset_for_boxplot

class DataAdapter(object):
    """DataAdapter(object)

    This class offers an adapter of OHLCV and related data used in pybitcoin.
    """
    def __init__(self, df=None, analysis_results=None, 
                 N_ema_min=1, N_ema_max=30, N_ema1=20, N_ema2=21, 
                 delta=10., N_dec=5, th_dec=0., **kwargs):
        """__init__(self, df=None, analysis_results=None, 
                    N_ema_min=10, N_ema_max=30, N_ema1=20, N_ema2=21, 
                    delta=10., N_dec=5, th_dec=0., **kwargs) -> None
        
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
        th_dec           : float (default : 5)
            threshold to average benefits on each pattern
        kwargs           : options
            api             : API class in pybitflyer
                an API instance
            product_code    : str (default : "FX_BTC_JPY")
                product code
            order_condition : str (default : "MARKET")
                market type
            size            : float (default : 1.0)
                size of BTC to order
        """
        self._data_frame = df
        self._analysis_results = analysis_results

        # for OHLCV
        self.N_ema_min = N_ema_min
        self.N_ema_max = N_ema_max
        self._N_ema1 = N_ema1
        self._N_ema2 = N_ema2
        self._N_macd = 14
        self._delta = delta # for judgement of extreme maxima / minima
        self.N_dec = N_dec
        self._th_dec = th_dec

        # for API of pybitflyer
        self._api = kwargs.get("api")
        if self._api is None:
            self._api = init_api()
        self._product_code = kwargs.get("product_code", "FX_BTC_JPY")
        self._order_condition = kwargs.get("order_condition", "MARKET")
        self._size = kwargs.get("size", 1.0)
        self._count = 500
        self._params_buy = {
            "product_code":self._product_code,
            "child_order_type":self._order_condition,
            "side":"buy",
            "size":self._size,
            "minute_to_expire":10
        }
        self._params_sell = {
            "product_code":self._product_code,
            "child_order_type":self._order_condition,
            "side":"sell",
            "size":self._size,
            "minute_to_expire":10
        }
        self._datetimeFmt = "%Y-%m-%dT%H:%M:%S.%f"
        self._datetimeFmt2 = "%Y-%m-%dT%H:%M:%S"

        # initialize inner data
        self._dead_patterns = None
        self._golden_patterns = None
        self._df_initialized = True
        self._ema_update = True
        self._delta_update = True
        self._benefit_timing = "worst" # in ["worst", "mean", "open"]
        self.updateAlpha()
        self.initOHLCVData()
        self.initOHLCVTmpData()
        # self.updateOHLCVRealTime(None)

        if self._analysis_results is not None:
            self._ana_set = True
        else:
            self._ana_set = False
        self._ana_update = False
        self.initAnalysisData()
    
    @footprint
    def initOHLCVData(self):
        """initInnerData(self) -> None

        initialize the inner data for OHLCV
        """
        if not hasattr(self, "_tmp_target"):
            self._tmp_target = [
                "N_ema1", "N_ema2", "ltp", "timestamp", "ohlc_list", 
                "oc_up_down", "dec", "volume_list", "close", 
                "ema1", "ema2", "cross_signal", "extreme_signal", 
                "current_max", "current_min", "look_for_max", "jpy_list", "benefit_list", 
                "current_state", "order_ltp", "stop_by_cross", 
            ]
        if self._df_initialized or self._ema_update or self._delta_update:
            self._ltp = []
            self._timestamp = []
            self._ohlc_list = []
            self._oc_up_down = []
            self._dec = []
            self._latest_id = None
            self._volume_list = []
            self._ema_update = True
            self._close = []
            self._ema1 = []
            self._ema2 = []
            self._macd = []
            self._macd_signal = []
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
            self._ii = 0
            if isinstance(self._data_frame, pd.DataFrame):
                if self._df_initialized or self._ema_update or self._delta_update:
                    self._data_ = self._data_frame[["open", "high", "low", "close"]].values
                    volume_ = self._data_frame["volume"].values
                    for ii, row in enumerate(self._data_):
                        self._ii = ii
                        # print(ii)
                        buff = np.zeros(5)
                        buff[0] = ii + 1
                        buff[1:] = row.copy()
                    
                        self._timestamp.append(ii + 1)
                        self._volume_list.append(volume_[ii])
                        self._ohlc_list.append(buff.copy())
                        self._close.append(row[-1])
                        self._oc_up_down.append(int(row[-1] > row[0]))
                        self._dec.append(self.calcDec())
                        self._ema1.append(self.calcEMA(self._ema1, self._alpha1))
                        self._ema2.append(self.calcEMA(self._ema2, self._alpha2))
                        self._macd.append(self.calcMACD(self._ema1, self._ema2))
                        self._macd_signal.append(self.calcMACDSignal(self._macd, self._alpha_macd))
                        self._cross_signal.append(self.judgeCrossPoint())
                        self._extreme_signal.append(self.judgeExtremePoint())
                        self.updateExecutionState()
                        self.orderProcess()
                    self._dec = np.array(self._dec, dtype=int)
                    # self._latest = 
                else:
                    pass
            else:
                raise TypeError('df must be a pandas.DataFrame object.')
        self._benefit_list = np.array(self._benefit_list)
        self._df_initialized = False
        self._ema_update = False
        self._delta_update = False
    
    def calcDec(self):
        """calcDec(self) -> int

        calculate the decimal value for the corresponding pattern
        """
        if len(self._dec) < self.N_dec:
            return 0
        else:
            return int("".join([str(i_) for i_ in self._oc_up_down[-self.N_dec:]]), 2)
    
    def calcEMA(self, ema_list, alpha):
        """calcEMA(self, ema_list, alpha) -> float

        calculate the EMA value for the latest close data

        Parameters
        ----------
        ema_list : array-like
            list of historical EMA values
        alpha    : float
            alpha parameter of EMA calculation
        
        Returns
        -------
        EMA : float
            current EMA value
        """
        if len(ema_list) == 0:
            return self._close[0]
        else:
            return (1. - alpha) * ema_list[-1] + alpha * self._close[self._ii]
    
    def calcMACD(self, ema1, ema2):
        """calcMACD(self, ema1, ema2) -> float

        calculate the MACD value

        Parameters
        ----------
        ema1 : array-like
            the first EMA
        ema2 : array-like
            the second EMA
        
        Returns
        -------
        MACD : float
            current MACD value
        """
        if len(ema1) == 0 or len(ema2) == 0:
            return 0.
        else:
            return ema1[-1] - ema2[-1]
    
    def calcMACDSignal(self, MACD, alpha):
        """calcMACDSignal(self, MACD, alpha) -> float

        calculate the MACD signal

        Parameters
        ----------
        MACD : array-like
            list of historical EMA values
        alpha    : float
            alpha parameter of EMA calculation
        
        Returns
        -------
        current EMA value (float)
        """
        if len(self._macd_signal) == 0:
            return self._macd[0]
        else:
            return (1. - alpha) * MACD[-1] + alpha * self._macd[self._ii]
    
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
        diff = self._ema1[-1] - self._ema2[-1]
        self._current_max = max([diff, self._current_max])
        self._current_min = min([diff, self._current_min])
        if self._look_for_max is None:
            value = 0.
        elif self._look_for_max and diff < self._current_max - self._delta:
            self._look_for_max = False
            self._current_min = diff
            value = 1.
        elif (not self._look_for_max) and diff > self._current_min + self._delta:
            self._look_for_max = True
            self._current_max = diff
            value = -1.
        else:
            value = 0.
        if self._current_state == "wait":
            return 0.
        else:
            return value
    
    def updateExecutionState(self):
        """updateExecutionState(self) -> None

        update the state of execution
        """
        if self._current_state == "wait":
            if self._cross_signal[-1] == 1.: # golden cross
                if self._golden_patterns is None or self._dec[-1] in self._golden_patterns:
                    self._current_state = "ask"
            if self._cross_signal[-1] == -1.: # dead cross
                if self._golden_patterns is None or self._dec[-1] in self._dead_patterns:
                    self._current_state = "bid"
        elif self._current_state == "sell":
            if self._cross_signal[-1] == -1. or self._extreme_signal[-1] == 1.:
                self._current_state = "con"
        elif self._current_state == "buy":
            if self._cross_signal[-1] == 1. or self._extreme_signal[-1] == -1.:
                self._current_state = "con"
        
    def orderProcess(self):
        """orderProcess(self) -> None

        process of order
        """
        if len(self._jpy_list) == 0:
            self._jpy_list.append(0)
        else:
            self._jpy_list.append(self._jpy_list[-1])
        self._benefit_list.append(0)
        # <debug>
        if self._ii == len(self._data_frame) - 1:
            return
        row = self._data_[self._ii + 1]
        # </debug>
        if self._benefit_timing == "worst":
            ltp_max = max([row[0], row[-1]])
            ltp_min = min([row[0], row[-1]])
        elif self._benefit_timing == "mean":
            ltp_max = int((row[0] + row[-1]) / 2)
            ltp_min = int((row[0] + row[-1]) / 2)
        elif self._benefit_timing == "open":
            ltp_max = row[0]
            ltp_min = row[0]
        else:
            raise ValueError
        if self._current_state == "ask": # order of "sell"
            self._order_ltp = ltp_max
            self._current_state = "sell"
            self._look_for_max = True
        elif self._current_state == "bid": # order of "buy"
            self._order_ltp = ltp_min
            self._current_state = "buy"
            self._look_for_max = False
        elif self._current_state == "con":
            # when the previous state is "sell"
            ## a dead cross point reaches before the first extreme maximum point
            if self._cross_signal[-1] == -1.:
                # order of "sell"
                ltp_ = ltp_min
                self._jpy_list[-1] += ltp_ - self._order_ltp
                self._benefit_list[-1] += ltp_ - self._order_ltp
                self._stop_by_cross = 0

                # go to bid and order immediately
                self._order_ltp = ltp_min
                self._current_state = "buy"
                self._look_for_max = False
            
            ## the first extreme maximum point reaches before a dead cross point
            elif self._extreme_signal[-1] == 1.:
                # order of "sell"
                ltp_ = ltp_min
                self._jpy_list[-1] += ltp_ - self._order_ltp
                self._benefit_list[-1] += ltp_ - self._order_ltp
                self._order_ltp = 0
                self._current_state = "wait"
                self._look_for_max = None

            # when the previous state is "buy"
            ## a golden cross point reaches before the first extreme minimum point
            elif self._cross_signal[-1] == 1.:
                # order of "buy"
                ltp_ = ltp_max
                self._jpy_list[-1] -= ltp_ - self._order_ltp
                self._benefit_list[-1] -= ltp_ - self._order_ltp
                self._stop_by_cross = 0

                # go to ask and order immediately
                self._order_ltp = ltp_max
                self._current_state = "sell"
                self._look_for_max = True
            
            ## the first extreme minimum point reaches before a golden cross point
            elif self._extreme_signal[-1] == -1.:
                # order of "buy"
                ltp_ = ltp_max
                self._jpy_list[-1] -= ltp_ - self._order_ltp
                self._benefit_list[-1] -= ltp_ - self._order_ltp
                self._order_ltp = 0
                self._current_state = "wait"
                self._look_for_max = None
        else:
            return
        
    def initOHLCVTmpData(self):
        """initOHLCTmpData(self) -> None

        initialize temporary data of OHLCV
        """
        self._latest = None # latest timestamp
        self._tmp_ohlc = []
        self._ltp = np.empty(0, dtype=int)
        self._tmp_ltp = np.empty(0, dtype=int) # for temporal stock
        self._tmp_volume = np.empty(0, dtype=float)
        self._t_start = None
        self._t_next = None
        self._t_end = None
        self._id_start = None
        self._id_next = None
        self._id_end = None
        self._df_new = None
    
    @footprint
    def initAnalysisData(self):
        """initAnalysisData(self) -> None

        initialize the inner data for analysis
        """
        try:
            if self._ana_set:
                if isinstance(self._analysis_results, dict):
                    buff = np.zeros((self.N_ema_max + 1, self.N_ema_max + 1), dtype=int)
                    self._benefit_map = self._analysis_results.get("benefit_map", buff)
                    self._stat_dead_list = self._analysis_results.get("stat_dead_list", [])
                    self._stat_golden_list = self._analysis_results.get("stat_golden_list", [])
                    self._dec_dead_box_list = self._analysis_results.get("dec_dead_box_list", [])
                    self._dec_golden_box_list = self._analysis_results.get("dec_golden_box_list", [])
                    self._dec_dead_list = self._analysis_results.get("dec_dead_list", [])
                    self._dec_golden_list = self._analysis_results.get("dec_golden_list", [])
                    self._dead_patterns = self._analysis_results.get("dead_patterns")
                    self._golden_patterns = self._analysis_results.get("golden_patterns")
                else:
                    raise TypeError('analysis_results must be a dict object.')
            elif self._ana_update:
                self._benefit_map = np.zeros((self.N_ema_max + 1, self.N_ema_max + 1), dtype=int)
                self._stat_dead_list = []
                self._stat_golden_list = []
                self._dec_dead_box_list = []
                self._dec_golden_box_list = []
                self._dec_dead_list = []
                self._dec_golden_list = []
                # reserve the current dataset temporaly
                for s in self._tmp_target:
                    exec("tmp_{0} = copy.deepcopy(self._{0})".format(s))
                
                # calculate statistics and benefits for each pair (N_ema1, N_ema2)
                for ii, kk in combinations(np.arange(0, self.N_ema_max - self.N_ema_min + 1), 2):
                # for ii in range(self.N_ema_min, self.N_ema_max):
                #     for kk in range(ii, self.N_ema_max):
                    # calculate a dataset of signals
                    self._N_ema1 = self.N_ema_min + ii
                    self._N_ema2 = self.N_ema_min + kk
                    self._ema_update = True
                    self.updateAlpha()
                    self.initOHLCVData()
                    self._benefit_map[ii + 1, kk + 1] = 1*self._jpy_list[-1]

                    # distribute temporal benefits to patterns
                    dec_dead = [np.empty(0)] * 2**self.N_dec
                    dec_golden = [np.empty(0)] * 2**self.N_dec
                    for jj in range(len(self._cross_signal)):
                        if self._cross_signal[jj] == 1: # golden case
                            buff = self._benefit_list[jj:]
                            # buff2 = np.array(self._extreme_signal[jj:], dtype=float)
                            # v = buff[np.where(buff2 == 1.)[0][0] + 1]
                            ind = buff != 0
                            if ind.sum() != 0:
                                v = buff[buff != 0][0]
                            else:
                                v = 0
                            dec_golden[self._dec[jj]] = \
                                np.append(dec_golden[self._dec[jj]], v)
                        elif self._cross_signal[jj] == -1: # dead case
                            buff = self._benefit_list[jj:]
                            # buff2 = np.array(self._extreme_signal[jj:], dtype=float)
                            # v = buff[np.where(buff2 == -1.)[0][0] + 1]
                            ind = buff != 0
                            if ind.sum() != 0:
                                v = buff[buff != 0][0]
                            else:
                                v = 0
                            dec_dead[self._dec[jj]] = \
                                np.append(dec_dead[self._dec[jj]], v)
                    
                    # make datasets for boxplot
                    dec_dead_box = []
                    dec_golden_box = []
                    for jj in range(2**self.N_dec):
                        dec_dead_box.append(
                            dataset_for_boxplot(dec_dead[jj], jj)
                        )
                        dec_golden_box.append(
                            dataset_for_boxplot(dec_golden[jj], jj)
                        )
                    
                    # calculate statistics
                    stat_dead = np.zeros((2**self.N_dec, 5), dtype=float)
                    stat_golden = np.zeros((2**self.N_dec, 5), dtype=float)
                    for jj in range(2**self.N_dec):
                        # golden case
                        arr = dec_golden[jj]
                        if len(arr) != 0:
                            ind = np.abs(arr) <=100000
                            dec_golden[jj] = arr[ind]
                            stat_golden[jj] = np.array([
                                arr[ind].max(), 
                                arr[ind].min(), 
                                arr[ind].mean(), 
                                arr[ind].std(), 
                                np.median(arr[ind])
                            ])
                        # dead case
                        arr = dec_dead[jj]
                        if len(arr) != 0:
                            ind = np.abs(arr) <=100000
                            dec_dead[jj] = arr[ind]
                            stat_dead[jj] = np.array([
                                arr[ind].max(), 
                                arr[ind].min(), 
                                arr[ind].mean(), 
                                arr[ind].std(), 
                                np.median(arr[ind])
                            ])
                        
                    # append
                    self._dec_golden_list.append(dec_golden)
                    self._dec_dead_list.append(dec_dead)
                    self._dec_golden_box_list.append(dec_golden_box)
                    self._dec_dead_box_list.append(dec_dead_box)
                    self._stat_golden_list.append(stat_golden)
                    self._stat_dead_list.append(stat_dead)
                
                # set the preserved dataset to the inner parameters
                for s in self._tmp_target:
                    exec("self._{0} = copy.deepcopy(tmp_{0})".format(s))
                self.updateAlpha()
            self._ana_set = False
            self._ana_update = False
        except Exception as ex:
            _, _2, exc_tb = sys.exc_info()
            # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("line {}: {}".format(exc_tb.tb_lineno, ex))
    
    def updateAlpha(self):
        """updateAlpha(self) -> None

        update the alpha parameters for calulation of EMA
        """
        self._alpha1 = 2. / (self._N_ema1 + 1.)
        self._alpha2 = 2. / (self._N_ema2 + 1.)
        self._alpha_macd = 2. / (self._N_macd + 1.)
    
    def updateOHLCVData(self):
        """updateOHLCVData(self) -> None

        update OHLCV data
        """
        params = {
            "product_code":self._product_code,
            "count":self._count,
            "before":self._id_next + self._count + 1,
        }
        ## get executions
        is_success = False
        fault_count = 0
        while not is_success:
            try:
                results = self._api.executions(**params)[::-1]
                is_success = True
            except:
                fault_count += 1
                continue
        
        ## extract
        ids_ = np.array([_res["id"] for _res in results], dtype=int)
        ltps_ = np.array([_res["price"] for _res in results], dtype=int)
        volumes_ = np.array([_res["size"] for _res in results], dtype=float)
        datetimes_ = []
        for _res in results:
            try:
                datetimes_.append(datetime.strptime(_res["exec_date"], self._datetimeFmt))
            except ValueError:
                datetimes_.append(datetime.strptime(_res["exec_date"], self._datetimeFmt2))
        datetimes_ = np.array(datetimes_)

        ## find valid indices & extract
        ind_id = ids_ >= self._id_next
        ind_now = (datetimes_ >= self._t_start) & (datetimes_ < self._t_next)
        ind_next = datetimes_ >= self._t_next
        self._ltp = np.hstack((self._ltp, ltps_[ind_id&ind_now]))
        self._tmp_ltp = np.hstack((self._tmp_ltp, ltps_[ind_id&ind_now]))
        self._tmp_volume = np.hstack((self._tmp_volume, volumes_[ind_id&ind_now]))
        
        ## processing for next step
        # if (ind_id&ind_now).sum() == 0:
        #     id_start_ = 
        #     continue
        if ind_next.sum() == 0:
            self._id_next = 1*(ids_[ind_id&ind_now])[-1]
        else:
            timestamp_ = self._t_start.timestamp()
            id_end_ = 1*(ids_[ind_id&ind_next])[0] - 1
            self._tmp_ohlc.append([
                timestamp_, 
                self._id_start, 
                self._id_end, 
                self._tmp_ltp[0], 
                self._tmp_ltp.max(), 
                self._tmp_ltp.min(), 
                self._tmp_ltp[-1], 
                self._tmp_volume.sum()
            ])
            self._id_start = id_end_ + 1
            self._id_next = 1*(ids_[ind_id&ind_next])[-1]
            self._tmp_ltp = np.empty(0, dtype=int)
            self._tmp_ltp = np.hstack((self._tmp_ltp, ltps_[ind_id&ind_next]))
            self._tmp_volume = np.empty(0, dtype=float)
            self._tmp_volume = np.hstack((self._tmp_volume, volumes_[ind_id&ind_next]))
            self._t_start += timedelta(minutes=1)
            self._t_next += timedelta(minutes=1)
            print("next id:{}, datetime:{}".format(self._id_start, self._t_start.strftime("%Y-%m-%dT%H:%M:%S")))
    
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
        if self._analysis_results is not None:
            self._ana_set = True
            self.initAnalysisData()
    
    @property
    def N_ema1(self):
        return self._N_ema1
    
    @N_ema1.setter
    def N_ema1(self, N):
        self._N_ema1 = N
        self._alpha1 = 2./(self._N_ema1 + 1.)
        self._ema_update = True
    
    @property
    def N_ema2(self):
        return self._N_ema2
    
    @N_ema2.setter
    def N_ema2(self, N):
        self._N_ema2 = N
        self._alpha2 = 2./(self._N_ema2 + 1.)
        self._ema_update = True
    
    @property
    def delta(self):
        return self._delta
    
    @delta.setter
    def delta(self, v):
        self._delta = v
        self._delta_update = True
    
    @property
    def th_dec(self):
        return self._th_dec
    
    @th_dec.setter
    def th_dec(self, v):
        self._th_dec = v

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
    def benefit_list(self):
        return self._benefit_list
    
    @property
    def dec(self):
        return self._dec
    
    @property
    def current_state(self):
        return self._current_state
    
    @property
    def order_ltp(self):
        return self._order_ltp
    
    @property
    def ana_update(self):
        return self._ana_update
    
    @ana_update.setter
    def ana_update(self, v):
        self._ana_update = v
    
    @property
    def benefit_map(self):
        return self._benefit_map

    @property
    def dec_dead_box_list(self):
        return self._dec_dead_box_list
    
    @property
    def dec_golden_box_list(self):
        return self._dec_golden_box_list

    @property
    def dec_dead_list(self):
        return self._dec_dead_list
    
    @property
    def dec_golden_list(self):
        return self._dec_golden_list
    
    @property
    def stat_dead_list(self):
        return self._stat_dead_list
    
    @property
    def stat_golden_list(self):
        return self._stat_golden_list
    
    @property
    def benefit_timing(self):
        return self._benefit_timing
    
    @benefit_timing.setter
    def benefit_timing(self, v):
        if v in ["worst", "mean", "open"]:
            self._benefit_timing = v
        else:
            print("'{}'must be one of ['worst', 'mean', 'open']".format(v))
    
    def register(self):
        """register(self) -> None

        register patterns
        """
        mean = self._stat_dead_list[self._N_ema1][:, 2]
        self._dead_patterns = np.arange(2**self.N_dec)[mean > self._th_dec]

        mean = self._stat_golden_list[self._N_ema1][:, 2]
        self._golden_patterns = np.arange(2**self.N_dec)[mean > self._th_dec]
    
    def unregister(self):
        """unregister(self) -> None

        unregister patterns
        """
        self._dead_patterns = None
        self._golden_patterns = None

    def dataset_for_chart_graphs(self, start=0, end=None):
        """dataset_for_chart_graphs(self) -> dict   
        return a dataset for plotting in ChartGraphs class.

        Parameters
        ----------
        start : int
            start index to return
        end   : int
            end index to return
        
        Returns
        -------
        obj : dict
            obj has the following key-value pairs:
                timestamp      : 1-dimensional array-like
                    timestamp
                ohlc           : 2-dimensional array-like
                    ohlc
                volume         : 1-dimensional array-like
                    volume
                ema1           : 1-dimensional array-like
                    1st EMA curve
                ema2           : 1-dimensional array-like
                    2nd EMA curve
                cross_signal   : 1-dimensional array-like
                    cross points of 1st & 2nd EMAs
                extreme_signal : 1-dimensional array-like
                    signal for extreme points of difference btwn. 1st & 2nd EMAs
                jpy_list       : 1-dimensional array-like
                    revolution of stock
        """

        if end is None:
            end = len(self._timestamp)
        obj = {
            "timestamp":self._timestamp[start:end], 
            "ohlc":self._ohlc_list[start:end], 
            "volume":self._volume_list[start:end], 
            "ema1":self._ema1[start:end], 
            "ema2":self._ema2[start:end], 
            "cross_signal":self._cross_signal[start:end], 
            "extreme_signal":self._extreme_signal[start:end], 
            "jpy_list":self._jpy_list[start:end]
        }
        return obj
    
    def dataset_for_analysis_graphs(self, N_ema1=None, N_ema2=None):
        """dataset_for_analysis_graphs(self, N_ema1=None, N_ema2=None) -> dict   
        return a dataset for plotting in AnalysisGraphs class.

        Parameters
        ----------
        N_ema1 : int (default : None)
            N number for the first EMA line
        N_ema2 : int (default : None)
            N number for the second EMA line

        Returns
        -------
        obj : dict
            obj has the following key-value pairs:   
                benefit_map    : numpy.2darray
                    map of benefit
                N_dec          : int
                    the exponent of the decimal for OHLC patterns
                stat_dead      : numpy.2darray with the shape of (2**N_dec, 5)
                    statistics of the benefit in dead-cross orders
                stat_golden    : numpy.2darray with the shape of (2**N_dec, 5)
                    statistics of the benefit in golden-cross orders
                dec_dead_box   : list of tuples with the length of 2**N_dec
                    list of the benefits in dead-cross orders
                dec_golden_boc : list of tuples with the length of 2**N_dec
                    list of the benefits in golden-cross orders
        """

        if N_ema1 is None:
            N_ema1 = self.N_ema_min
        if N_ema2 is None:
            N_ema2 = N_ema1 + 1
        index = 0
        for ii, kk in combinations(np.arange(0, self.N_ema_max - self.N_ema_min + 1), 2):
            if ii == N_ema1 - self.N_ema_min:
                if kk == N_ema2 - self.N_ema_min - 1:
                    break
            index += 1
        obj = {
            "N_dec":self.N_dec, 
            "benefit_map":self._benefit_map, 
            "dec_dead_box":self._dec_dead_box_list[N_ema1 - self.N_ema_min], 
            "dec_golden_box":self._dec_golden_box_list[N_ema1 - self.N_ema_min], 
            "stat_dead":self._stat_dead_list[N_ema1 - self.N_ema_min], 
            "stat_golden":self._stat_golden_list[N_ema1 - self.N_ema_min]
        }
        return obj
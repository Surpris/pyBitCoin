#! /usr/bin/python3
# -*- coding: utf-8 -*-

"""
Worker.py
This file offers the following items:

* Worker
* GetTickerWorker
* AnalysisWorker
"""

import numpy as np
import pybitflyer
from PyQt5.QtCore import QMutex, QMutexLocker, pyqtSignal, QObject, pyqtSlot
import time

try:
    from ..utils import DataAdapter
except:
    import sys
    sys.path.append("../")
    from utils import DataAdapter


class Worker(QObject):
    do_something = pyqtSignal(object)
    do_something2 = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, name = "", parent = None, debug=False):
        super().__init__(parent)
        self.mutex = QMutex()
        self.name = name
        self.DEBUG = debug
        self.data = None
        self.stopWorking = False
        self.sleepInterval = 1

    @pyqtSlot()
    def process(self):
        """process(self) -> None

        This function is to be connected with a pyqtSignal object on another thread.
        """
        st = time.time()
        try:
            with QMutexLocker(self.mutex):
                self._process()
        except Exception as ex:
            print(ex)
        self.do_something.emit(self.data)
        self.do_something2.emit(self.data)
        elapsed = time.time() - st
        if self.DEBUG:
            print("Elapsed time of process:{0:.4f} sec.".format(elapsed))
        self.finished.emit()

    def _process(self):
        """_process(self) -> None

        Something to do should described in this function.
        """
        print("sleep")
        time.sleep(10)
        self.data = "Test"
        self.isStopped = True

class GetTickerWorker(Worker):
    def __init__(self, name = "", parent = None, api=None, product_code=None, adapter=None, debug=False):
        super().__init__(name=name, parent=parent, debug=debug)
        self._api = api
        self._product_code = product_code
        self._adapter = adapter
        self._count = 200

    def _process(self):
        """_process(self) -> None

        get information from bitFlyer
        """
        market_data = self._api.ticker(product_code=self._product_code)
        # balance = self._api.getbalance()
        collateral = self._api.getcollateral()
        health = self._api.getboardstate()
        dataset = self._adapter.updateOHLCVData()
        # executions = self._api.executions(product_code=self._product_code, count=self._count)
        self.data = {
            "market_data":market_data, 
            "collateral":collateral,
            # "balance":balance,
            "health":health,
            "dataset":dataset,
        }

# class AnalysisWorker(Worker):
#     def __init__(self, name = "", parent = None, data_adapter = None):
#         """__init__(self, name = "", parent = None, data_adapter = None) -> None
        
#         initialize this class
#         """
#         super().__init__(name=name, parent=parent, debug=False)
#         self.dataset = None
#         self.N_ema_max = N_ema_max
#         self.N_ema_min = N_ema_min
#         self.N_dec = N_dec
#         self.delta = delta

#     def _process(self):
#         """_process(self) -> None
#         analyze OHLCV dataset
#         """
#         st = time.time()
#         # stat_dead_list = []
#         # stat_golden_list = []
#         # ext_dead_list = []
#         # ext_golden_list = []
#         # cross_points_list = []
#         results_list = []
#         benefit_map = np.zeros((self.N_ema_max + 1, self.N_ema_max + 1), dtype=int)
#         for ii in range(self.N_ema_min, self.N_ema_max):
#             results = analyze(self.dataset, ii, ii + 1, self.N_dec, self.delta)

#             # extract benefit
#             benefits = results["benefits"]
#             a_k = results["a_k"]
#             dead_ = -benefits[a_k[:, 1] == -1].sum()
#             golden_ = benefits[a_k[:, 1] == 1].sum()
#             benefit_map[ii, ii + 1] = dead_ + golden_

#             results_list.append(results)

#             # extract 
#             # cross_points_list.append(results["cross_points"])
#             # stat_dead_list.append(results["stat_dead"])
#             # stat_golden_list.append(results["stat_golden"])
#             # ext_dead_list.append(results["list_ext_dead"])
#             # ext_golden_list.append(results["list_ext_golden"])
        
#         self.data = {
#             "benefit_map":benefit_map,
#             "results_list":results_list,
#             # "cross_points_list":cross_points_list,
#             # "stat_dead_list":stat_dead_list,
#             # "stat_golden_list":stat_golden_list,
#             # "ext_dead_list":ext_dead_list,
#             # "ext_golden_list":ext_golden_list
#         }
#         print("finish analysis.")
#         print("Elapsed time: {0:.2f} sec.".format(time.time() - st))

class AnalysisWorker(Worker):
    def __init__(self, name = "", parent = None, adapter = None):
        """__init__(self, name = "", parent = None, adapter = None) -> None
        
        initialize this class

        Parameters
        ----------
        name    : str
            name of an instance
        parent  : instance of a class overtaking QtWidgets
            parent of the instance
        adapter : DataAdapter
            data adapter of OHLCV dataset
        """
        super().__init__(name=name, parent=parent, debug=False)
        self.adapter = adapter

    def _process(self):
        """_process(self) -> None

        analyze OHLCV dataset
        """
        print("AnalysisWorker.process(): start.")
        st = time.time()
        self.adapter.ana_update = True
        self.adapter.initAnalysisData()
        self.data = {
            "benefit_map":self.adapter.benefit_map, 
            "stat_dead_list":self.adapter.stat_dead_list, 
            "stat_golden_list":self.adapter.stat_golden_list, 
            "dec_dead_box_list":self.adapter.dec_dead_box_list, 
            "dec_golden_box_list":self.adapter.dec_golden_box_list, 
            "dec_dead_list":self.adapter.dec_dead_list, 
            "dec_golden_list":self.adapter.dec_golden_list, 
        }
        print("AnalysisWorker.process(): finish. {0:.2f} sec.".format(time.time() - st))
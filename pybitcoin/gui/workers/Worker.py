#! /usr/bin/python3
# -*- coding: utf-8 -*-

import pybitflyer
from PyQt5.QtCore import QMutex, QMutexLocker, pyqtSignal, QObject, pyqtSlot
import time

class Worker(QObject):
    do_something = pyqtSignal(object)
    do_something2 = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, name = "", parent = None):
        super().__init__(parent)
        self.mutex = QMutex()
        self.name = name
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
        print("Elapsed time of process:{0:.4f} sec.".format(elapsed))
        self.finished.emit()

    def _process(self):
        """
        Something to do should descriibed in this function.
        """
        print("sleep")
        time.sleep(10)
        self.data = "Test"
        self.isStopped = True

class GetTickerWorker(Worker):
    def __init__(self, name = "", parent = None, api=None, product_code=None):
        super().__init__(name=name, parent=parent)
        self._api = api
        self._product_code = product_code

    def _process(self):
        market_data = self._api.ticker(product_code=self._product_code)
        # balance = self._api.getbalance()
        collateral = self._api.getcollateral()
        health = self._api.getboardstate()
        self.data = {
            "market_data":market_data, 
            "collateral":collateral,
            # "balance":balance,
            "health":health
        }

# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 18:29:00 2017

@author: Surpris
"""

import sys
import os
import datetime
import numpy as np
import time
import json
from PyQt5.QtCore import QThread, QMutex, QMutexLocker, pyqtSignal, QObject, pyqtSlot
import pybitflyer

class WorkerThread(QThread):
    do_something = pyqtSignal()

    def __init__(self, name = "", parent = None):
        super().__init__(parent)
        self.sleep_interval = 900
        self.mutex = QMutex()
        self.name = name
        self.isStopped = False

    def run(self):
        while not self.isStopped:
        # while True:
            self.mutex.lock()
            self.do_something.emit()
            self.mutex.unlock()
            self.msleep(self.sleep_interval)
        self.finished.emit()
        print(self.name + " finished.")

    def stop(self):
        with QMutexLocker(self.mutex):
            self.isStopped = True

class Worker(QObject):
    do_something = pyqtSignal(object)
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
        """
        This function is to be connected with a pyqtSignal object on another thread.
        """
        # print(">> process():", os.getpid(), QThread.currentThread(), QThread.currentThreadId())
        # self.stopWorking = False
        # while not self.stopWorking:
        st = time.time()
        try:
            with QMutexLocker(self.mutex):
                self._process()
        except Exception as ex:
            print(ex)
                # self.stopWorking = True
        self.do_something.emit(self.data)
        elapsed = time.time() - st
        print("Elapsed time of process:{0:.4f} sec.".format(elapsed))
        # if elapsed < self.sleepInterval:
        #     time.sleep(self.sleepInterval - elapsed)
        self.finished.emit()

    @pyqtSlot(object)
    def process2(self, obj):
        """
        This function stops the thread calling this object.
        """
        print(">> process():", os.getpid(), QThread.currentThread(), QThread.currentThreadId())
        self.stopWorking = False
        while not self.stopWorking:
            try:
                with QMutexLocker(self.mutex):
                    self._process()
            except Exception as ex:
                print(ex)
                self.stopWorking = True
        self.do_something.emit(self.data)
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
        balance = self._api.getbalance()
        health = self._api.getboardstate()
        self.data = {
            "market_data":market_data, 
            "balance":balance,
            "health":health
        }
        # self.stopWorking = True

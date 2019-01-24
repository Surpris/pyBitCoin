#! /usr/bin/python3
#-*- coding:utf-8 -*-

"""
ChartGraphs.py
This file offers the following items:

* ChartGraphs
"""

import numpy as np
from PyQt5.QtWidgets import QGridLayout, QWidget, QLabel
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, pyqtSlot
import pyqtgraph as pg

import sys
sys.path.append("../")
import time

try:
    from CustomGraphicsItem import CandlestickItem
except ImportError:
    from .CustomGraphicsItem import CandlestickItem

from utils import make_groupbox_and_grid, make_pushbutton, make_label
from utils import footprint

class ChartGraphs(QWidget):
    """ChartGraphs class
    
    This class offers an window to plot the results of analysis of OHLCV datasets.
    """

    def __init__(self, parent = None, name = "", **kwargs):
        """__init__(self, parent = None, name = "", **kwargs) -> None

        initialize this class
        """
        super().__init__(parent)
        self.setParent(parent)
        self.name = name
        self.kwargs = kwargs
        self.initInnerParameters()
        self.initGui()
    
    @footprint
    def initInnerParameters(self):
        """initInnerParameters(self) -> None

        initialize the inner parameters
        """
        self.is_closed = False
        self._init_window_width = 400 # [pixel]
        self._init_window_height = 600 # [pixel]
        self._font_size_groupbox_title = 11 # [pixel]
        self._font_size_label = 11

        self._color_ema1 = "#3C8CE7"
        self._color_ema2 = "#EE8F1D"
        self._color_cross_signal = "#FFFFFF"
        self._color_extreme_signal = "#E8EE1D"
        self._color_stock = "#FFFFFF"

        self._DEBUG = False

    @footprint
    def initGui(self):
        """initGui(self) -> None

        initialize the GUI
        """
        # initialize the main
        self.resize(self._init_window_width, self._init_window_height)
        grid = QGridLayout(self)
        grid.setSpacing(10)

        # graphs
        self.glw = pg.GraphicsLayoutWidget()

        ## OHLC chart
        self.chart_ohlc = self.glw.addPlot()

        ## volume chart
        self.glw.nextRow()
        self.chart_volume = self.glw.addPlot()
        self.chart_volume.setMaximumHeight(self._init_window_height // 6)

        ## signal chart
        self.glw.nextRow()
        self.chart_signal = self.glw.addPlot()
        self.chart_signal.setMaximumHeight(self._init_window_height // 6)

        ## stock chart
        self.glw.nextRow()
        self.chart_stock = self.glw.addPlot()
        self.chart_stock.setMaximumHeight(self._init_window_height // 6)

        grid.addWidget(self.glw, 1, 0)
    
    @pyqtSlot(object)
    def updateGraphs(self, obj):
        """updateGraphs(self, obj) -> None

        update graphs

        Parameters
        ----------
        obj : dict
            obj must have the following key-value pairs:
                timestamp      : 1-dimensional array-like
                ohlc           : 2-dimensional array-like
                volume         : 1-dimensional array-like
                ema1           : 1-dimensional array-like
                ema2           : 1-dimensional array-like
                cross_signal   : 1-dimensional array-like
                extreme_signal : 1-dimensional array-like
                jpy_list       : 1-dimensional array-like
        """
        try:
            timestamp = obj["timestamp"]
            self.chart_ohlc.clear()
            self.chart_ohlc.addItem(CandlestickItem(obj["ohlc"]))
            self.chart_ohlc.plot(
                np.arange(timestamp[0], timestamp[-1] + 1), obj["ema1"], 
                clear=False, pen=pg.mkPen(self._color_ema1, width=2)
            )
            self.chart_ohlc.plot(
                np.arange(timestamp[0], timestamp[-1] + 1), obj["ema2"], 
                clear=False, pen=pg.mkPen(self._color_ema2, width=2)
            )
            
            self.chart_volume.clear()
            self.chart_volume.plot(
                np.arange(timestamp[0], timestamp[-1] + 1), obj["volume"], 
                clear=False, pen=pg.mkPen("#FFFFFF", width=2)
            )

            self.chart_signal.clear()
            self.chart_signal.plot(
                np.arange(timestamp[0], timestamp[-1] + 1), obj["cross_signal"], 
                clear=False, pen=pg.mkPen(self._color_cross_signal, width=2)
            )
            self.chart_signal.plot(
                np.arange(timestamp[0], timestamp[-1] + 1), obj["extreme_signal"], 
                clear=False, pen=pg.mkPen(self._color_extreme_signal, width=2)
            )

            self.chart_stock.clear()
            self.chart_stock.plot(
                np.arange(timestamp[0], timestamp[-1] + 1), obj["jpy_list"], 
                clear=False, pen=pg.mkPen(self._color_stock, width=2)
            )
        except Exception as ex:
            print(ex)
    
    @footprint
    def plotInDebugMode(self):
        if not self.DEBUG:
            raise Exception("`plotInDebugMode` is supported only in the debug mode.")
        
        timestamp = np.arange(1, 100)
        ohlc = []
        for ii in range(len(timestamp)):
            buff = np.zeros(5, dtype=int)
            buff[0] = ii + 1
            buff[1:] = np.random.randint(100, 150, 4)
            ohlc.append(buff)
        volume = np.random.randint(100, 150, len(timestamp))
        ema1 = np.random.randint(100, 150, len(timestamp))
        ema2 = np.random.randint(100, 150, len(timestamp))
        cross_signal = np.random.randint(-1, 2, len(timestamp))
        extreme_signal = np.random.randint(-1, 2, len(timestamp))
        jpy_list = np.random.randint(0, 100, len(timestamp))

        obj = {
            "timestamp":timestamp, "ohlc":ohlc, "volume":volume, 
            "ema1":ema1, "ema2":ema2, "cross_signal":cross_signal, 
            "extreme_signal":extreme_signal, "jpy_list":jpy_list
        }
        self.updateGraphs(obj)
    
    @property
    def DEBUG(self):
        return self._DEBUG

    @DEBUG.setter
    def DEBUG(self, v):
        self._DEBUG = v
        if self.DEBUG:
            self.setWindowTitle("AnalysisGraphs(Debug)")

def main():
    app = QApplication([])
    mw = ChartGraphs()
    mw.show()
    mw.DEBUG = True
    mw.plotInDebugMode()
    app.exec_()

if __name__ == "__main__":
    main()
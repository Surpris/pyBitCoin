#! /usr/bin/python3
#-*- coding:utf-8 -*-

"""
ChartWindow.py
This file offers the following items:

* ChartWindow
"""
import copy
from datetime import datetime
import numpy as np
import os
import pandas as pd
from PyQt5.QtWidgets import QMainWindow, QDialog, QGridLayout, QMenu, QWidget, QLabel, QLineEdit, QTextEdit
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot
# from PyQt5.QtChart import QChartView, QChart
import pyqtgraph as pg

import sys
sys.path.append("../")
from utils import make_groupbox_and_grid, make_pushbutton, calc_EMA, get_rate_via_crypto
from CustomGraphicsItem import CandlestickItem
# from .CustomGraphicsItem import CandlestickItem


class ChartWindow(QDialog):
    """ChartWindow class
    This class offers an window to draw candlesticks on.
    """

    def __init__(self, *args):
        """__init__(self, *args) -> None
        initialize this class
        """
        super().__init__(*args)

        self.initInnerParameters()
        self.initGui()
    
    def initInnerParameters(self):
        """initInnerParameters(self) -> None
        initialize the inner parameters
        """
        self._window_width = 600 # [pixel]
        self._window_height = 450 # [pixel]
        self._spacing = 5 # [pixel]
        self._groupbox_title_font_size = 14
        self._window_color = "gray"
        self._txt_bg_color = "#D0D3D4"

        self._count = 0
        self._N_ema1 = 5
        self._N_ema2 = 20
        self._color_ema1 = "#3C8CE7"
        self._color_ema2 = "#EE8F1D"
        self._color_cross_signal = "#FFFFFF"
        # self._plot_width = 30
        self.initInnerData()
        self.updateAlpha()

        self.data = None
        self._datetimeFmt_BITFLYER = "%Y-%m-%dT%H:%M:%S.%f"
        self._datetimeFmt_BITFLYER_2 = "%Y-%m-%dT%H:%M:%S"
        self.DEBUG = True
    
    def initInnerData(self):
        """initInnerData(self) -> None
        initialize the inner data
        """
        self._timestamp = []
        self._latest = None
        self._tmp_ltp = []
        self._tmp_ohlc = []
        self._ltp = []
        self._ohlc_list = []
        self._close = []
        self._ema1 = []
        self._ema2 = []
        self._cross_signal = []

    def updateAlpha(self):
        """updateAlpha(self) -> None
        update the alpha parameters for calulation of EMA
        """
        self._alpha1 = 2./(self._N_ema1 + 1.)
        self._alpha2 = 2./(self._N_ema2 + 1.)
    
    def initGui(self):
        """initGui(self) -> None
        initialize the GUI
        """
        # self.setAttribute(Qt.WA_DeleteOnClose)
        self.initMainGrid()
        # self.setMenuBar()

        if self.DEBUG:
            self.setWindowTitle("CandleStick(Emulate)")
        else:
            self.setWindowTitle("CandleStick")
        
        # Plot area
        self.glw = pg.GraphicsLayoutWidget()
        self.glw.resize(self._window_width - 20, self._window_height - 20)

        self.chart = self.glw.addPlot()

        self.glw.nextRow()
        self.chart2 = self.glw.addPlot()
        self.chart2.setMaximumHeight(self._window_height // 4)
        self.grid.addWidget(self.glw, 0, 0, 2, 1)

        # Buttons in debug mode
        if self.DEBUG:
            group_debug, grid_debug = make_groupbox_and_grid(
                self, self._window_width - 20, self._window_width - 20,
                "DEBUG", self._groupbox_title_font_size, self._spacing
            )
            self.le_start = QLineEdit(group_debug)
            self.le_start.setText("0")
            # font = self.le_start.font()
            # font.setPointSize(self._button_font_size)
            # self.le_start.setFont(font)
            self.le_start.resize((self._window_width - 50)//3, 16)
            self.le_start.setStyleSheet("background-color:{};".format(self._txt_bg_color))
            self.le_start.setValidator(QIntValidator())

            self.le_end = QLineEdit(group_debug)
            self.le_end.setText("100")
            self.le_end.resize((self._window_width - 50)//3, 16)
            self.le_end.setStyleSheet("background-color:{};".format(self._txt_bg_color))
            self.le_end.setValidator(QIntValidator())

            self.button1 = make_pushbutton(
                self, 40, 16, "Update", 14, 
                method=lambda data: self.update(data), color=None, isBold=False
            )
            grid_debug.addWidget(self.le_start, 0, 0)
            grid_debug.addWidget(self.le_end, 0, 1)
            grid_debug.addWidget(self.button1, 0, 2)

            self.grid.addWidget(group_debug, 2, 0, 1, 1)
    
    def initMainGrid(self):
        """ initMainWidget(self) -> None
        initialize the main widget and its grid.
        """
        self.resize(self._window_width, self._window_height)
        self.setStyleSheet("background-color:{};".format(self._window_color))
        self.grid = QGridLayout(self)
        self.grid.setSpacing(5)
    
    @pyqtSlot(object)
    def update(self, data):
        """update(self, data) -> None
        update the inner data and graphs

        Parameters
        ----------
        data : dict
            data must contain the following key-value pairs:
                timestamp : unix time (str)
                ltp : latest trading price (int)
        """
        try:
            if not self.DEBUG:
                self.updateInnerData(data)
            else:
                self.updateInnterDataDebug()
            self.updatePlots()
        except Exception as ex:
            print(ex)
    
    def updateInnerData(self, data):
        """updateInnerData(self, data) -> None
        update the inner data

        Parameters
        ----------
        data : dict
            data must contain the following key-value pairs:
                timestamp : unix time (str)
                ltp : latest trading price (int)
        """
        try:
            timestamp_ = datetime.strptime(data["timestamp"], self._datetimeFmt_BITFLYER)
        except ValueError:
            timestamp_ = datetime.strptime(data["timestamp"], self._datetimeFmt_BITFLYER_2)
        if self._latest is None:
            self._latest = timestamp_
            self._timestamp.append(0)
        elif self._latest.minute < timestamp_.minute:
            self._latest = timestamp_
            self._timestamp.append(0)
            self._cross_signal.pop()
            self._cross_signal.append(self.judgeCrossPoint())
            self._ohlc_list.pop()
            self._ohlc_list.append(copy.deepcopy(self._tmp_ohlc))

            self._tmp_ohlc.clear()
            self._tmp_ltp.clear()
        else:
            self._close.pop()
            self._ema1.pop()
            self._ema2.pop()
            self._cross_signal.pop()
            self._ohlc_list.pop()
        
        self._ltp.append(data["ltp"])
        self._tmp_ltp.append(data["ltp"])
        self._close.append(self._tmp_ltp[-1])
        self._ema1.append(self.calcEMA(self._ema1, self._alpha1))
        self._ema2.append(self.calcEMA(self._ema2, self._alpha2))
        self._cross_signal.append(0)
        self._tmp_ohlc = [
            len(self._timestamp), 
            self._tmp_ltp[0], 
            max(self._tmp_ltp), 
            min(self._tmp_ltp), 
            self._tmp_ltp[-1]
        ]
        self._ohlc_list.append(copy.deepcopy(self._tmp_ohlc))
    
    def updateInnterDataDebug(self):
        """updateInnterDataDebug(self) -> None
        """
        if not self.DEBUG:
            raise ValueError("This method must be used in a debug mode.")
        self.initInnerData()

        start_ = int(self.le_start.text())
        end_ = int(self.le_end.text())
        data_ = self.data[["open", "high", "low", "close"]].values[start_:end_]
        for ii, row in enumerate(data_):
            buff = np.zeros(5)
            buff[0] = ii + 1
            buff[1:] = row.copy()
            self._timestamp.append(ii + 1)
            self._close.append(row[-1])
            self._ema1.append(self.calcEMA(self._ema1, self._alpha1))
            self._ema2.append(self.calcEMA(self._ema2, self._alpha2))
            self._cross_signal.append(self.judgeCrossPoint())
            self._ohlc_list.append(buff.copy())

    
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
    
    def updatePlots(self):
        """updatePlots(self) -> None
        update Grpahs
        """
        self.chart.clear()
        self.chart.addItem(CandlestickItem(self._ohlc_list))
        self.chart.plot(
            np.arange(1, len(self._timestamp) + 1), self._ema1, 
            clear=False, pen=pg.mkPen(self._color_ema1, width=2)
        )
        self.chart.plot(
            np.arange(1, len(self._timestamp) + 1), self._ema2,
            clear=False, pen=pg.mkPen(self._color_ema2, width=2)
        )
        self.chart2.plot(
            np.arange(1, len(self._timestamp) + 1), self._cross_signal,
            clear=False, pen=pg.mkPen(self._color_cross_signal, width=2)
        )

    def setData(self, data):
        """setData(self, data) -> None
        set data
        """
        if isinstance(data, pd.DataFrame):
            self.data = data
        elif isinstance(data, str):
            self.data = pd.read_csv(data, index_col=0)
        else:
            raise TypeError("The parameter 'data' must have either DataFrame or str.")
        self._count = 0

def main():
    app = QApplication([])
    # app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "python.png")))
    mw = ChartWindow()
    # data = [  ## fields are (time, open, close, min, max).
    #     (1., 10, 15, 5, 13),
    #     (2., 13, 20, 9, 17),
    #     (3., 17, 23, 11, 14),
    #     (4., 14, 19, 5, 15),
    #     (5., 15, 22, 8, 9),
    #     (6., 9, 16, 8, 15),
    # ]
    fpath = r'..\data\OHLC_20181211.csv'
    fpath = r'..\data\OHLCV_201812241200_to_201812311200.csv'
    mw.setData(fpath)
    mw.show()
    app.exec_()

if __name__ == "__main__":
    main()
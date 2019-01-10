#! /usr/bin/python3
#-*- coding:utf-8 -*-

"""
ChartWindow.py
This file offers the following items:

* ChartWindow
"""

import argparse
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
from utils import make_groupbox_and_grid, make_pushbutton, make_label, calc_EMA
from utils import get_rate_via_crypto, to_dataFrame
try:
    from CustomGraphicsItem import CandlestickItem
except ImportError:
    from .CustomGraphicsItem import CandlestickItem


class ChartWindow(QDialog):
    """ChartWindow class
    This class offers an window to draw candlesticks on.
    """

    def __init__(self, debug=False, *args):
        """__init__(self, *args) -> None
        initialize this class
        """
        super().__init__(*args)

        self.initInnerParameters(debug)
        self.initGui()
    
    def initInnerParameters(self, debug):
        """initInnerParameters(self, debug) -> None
        initialize the inner parameters

        Parameters
        ----------
        debug : bool
        """

        # for GUI
        self._window_width = 600 # [pixel]
        self._window_height = 450 # [pixel]
        self._spacing = 5 # [pixel]
        self._groupbox_title_font_size = 14
        self._label_font_size = 14
        self._window_color = "gray"
        self._txt_bg_color = "#D0D3D4"

        # for settings
        self._btc_volime = 1.
        self._count = 0
        self._N_ema1 = 5
        self._N_ema2 = 20
        self._delta = 1. # for judgement of extreme maxima / minima
        self._datetimeFmt_BITFLYER = "%Y-%m-%dT%H:%M:%S.%f"
        self._datetimeFmt_BITFLYER_2 = "%Y-%m-%dT%H:%M:%S"

        # for chart
        self._color_ema1 = "#3C8CE7"
        self._color_ema2 = "#EE8F1D"
        self._color_cross_signal = "#FFFFFF"
        self._color_extreme_signal = "#E8EE1D"
        self._color_stock = "#FFFFFF"

        # for CryptoCompare
        self._histoticks = "minute"
        self._limit = int(4*60 - 1)
        self.setCryptoCompareParam()
        
        # for inner data
        # self._plot_width = 30
        self.initInnerData()
        self.updateAlpha()

        # for DEBUG
        self.DEBUG = debug
        self.data = None
    
    def setCryptoCompareParam(self):
        """setCryptoCompareParam(self) -> None
        """
        self._params_cryptocomp = {
            "fsym": "BTC",
            "tsym": "JPY",
            "limit": str(self._limit),
            "e": "bitFlyerfx",
        }
    
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
        self._extreme_signal = []
        self._current_max = np.Inf
        self._current_min = -np.Inf
        self._look_for_max = None
        self._jpy_list = []
        self._current_state = "wait"
        self._order_ltp = 0
        self._stop_by_cross = False
        

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
        self.chart_signal = self.glw.addPlot()
        self.chart_signal.setMaximumHeight(self._window_height // 4)

        self.glw.nextRow()
        self.chart_stock = self.glw.addPlot()
        self.chart_stock.setMaximumHeight(self._window_height // 4)

        self.grid.addWidget(self.glw, 0, 0, 2, 5)

        # Settings
        group_setting, grid_setting = make_groupbox_and_grid(
            self, 60, (self._window_height) // 3,
            "Settings", self._groupbox_title_font_size, self._spacing
        )

        label_ema1 = make_label(
            self, "N1", self._label_font_size, True,
            Qt.AlignLeft
        )
        grid_setting.addWidget(label_ema1, 0, 0)

        self.le_ema1 = QLineEdit(group_setting)
        self.le_ema1.setText(str(self._N_ema1))
        # font = self.le_ema1.font()
        # font.setPointSize(self._button_font_size)
        # self.le_ema1.setFont(font)
        self.le_ema1.resize(40, 16)
        self.le_ema1.setStyleSheet("background-color:{};".format(self._txt_bg_color))
        self.le_ema1.setValidator(QIntValidator())
        grid_setting.addWidget(self.le_ema1, 0, 1)

        label_ema2 = make_label(
            self, "N2", self._label_font_size, True,
            Qt.AlignLeft
        )
        grid_setting.addWidget(label_ema2, 1, 0)

        self.le_ema2 = QLineEdit(group_setting)
        self.le_ema2.setText(str(self._N_ema2))
        # font = self.le_ema2.font()
        # font.setPointSize(self._button_font_size)
        # self.le_ema2.setFont(font)
        self.le_ema2.resize(40, 16)
        self.le_ema2.setStyleSheet("background-color:{};".format(self._txt_bg_color))
        self.le_ema2.setValidator(QIntValidator())
        grid_setting.addWidget(self.le_ema2, 1, 1)

        label_delta = make_label(
            self, "delta", self._label_font_size, True,
            Qt.AlignLeft
        )
        grid_setting.addWidget(label_delta, 2, 0)

        self.le_delta = QLineEdit(group_setting)
        self.le_delta.setText(str(self._delta))
        # font = self.le_delta.font()
        # font.setPointSize(self._button_font_size)
        # self.le_delta.setFont(font)
        self.le_delta.resize(40, 16)
        self.le_delta.setStyleSheet("background-color:{};".format(self._txt_bg_color))
        self.le_delta.setValidator(QDoubleValidator())
        grid_setting.addWidget(self.le_delta, 2, 1)

        self.grid.addWidget(group_setting, 0, 6, 1, 1)

        # Results
        group_results, grid_results = make_groupbox_and_grid(
            self, 60, (self._window_height) // 3,
            "Results", self._groupbox_title_font_size, self._spacing
        )
        label_benefit = make_label(
            group_results, "Benefit", self._label_font_size, True,
            Qt.AlignLeft
        )
        self.label_benefit_value = make_label(
            group_results, "0", self._label_font_size, True,
            Qt.AlignLeft
        )
        label_perday = make_label(
            group_results, "Per day", self._label_font_size, True,
            Qt.AlignLeft
        )
        self.label_perday_value = make_label(
            group_results, "0", self._label_font_size, True,
            Qt.AlignLeft
        )
        grid_results.addWidget(label_benefit, 0, 0)
        grid_results.addWidget(self.label_benefit_value, 1, 0)
        grid_results.addWidget(label_perday, 2, 0)
        grid_results.addWidget(self.label_perday_value, 3, 0)

        self.grid.addWidget(group_results, 1, 6, 1, 1)
        

        # Items in debug mode
        if self.DEBUG:
            group_debug, grid_debug = make_groupbox_and_grid(
                self, self._window_width - 20, 40,
                "DEBUG", self._groupbox_title_font_size, self._spacing
            )

            ## start position
            self.le_start = QLineEdit(group_debug)
            self.le_start.setText("0")
            # font = self.le_start.font()
            # font.setPointSize(self._button_font_size)
            # self.le_start.setFont(font)
            self.le_start.resize((self._window_width - 50)//3, 16)
            self.le_start.setStyleSheet("background-color:{};".format(self._txt_bg_color))
            self.le_start.setValidator(QIntValidator())

            ## end position
            self.le_end = QLineEdit(group_debug)
            self.le_end.setText("100")
            self.le_end.resize((self._window_width - 50)//3, 16)
            self.le_end.setStyleSheet("background-color:{};".format(self._txt_bg_color))
            self.le_end.setValidator(QIntValidator())

            ## update button
            self.button1 = make_pushbutton(
                self, 40, 16, "Update", 14, 
                method=lambda data: self.update(data), color=None, isBold=False
            )

            ## button to get OHLCV data from CryptoCompare
            self.button2 = make_pushbutton(
                self, 40, 16, "Get OHLC", 14, 
                method=self.getOHLC, color=None, isBold=False
            )

            ## add
            grid_debug.addWidget(self.le_start, 0, 0)
            grid_debug.addWidget(self.le_end, 0, 1)
            grid_debug.addWidget(self.button1, 0, 2)
            grid_debug.addWidget(self.button2, 0, 3)

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
                self.updateInnerDataDebug()
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
            self._extreme_signal.append(self.judgeExtremePoint())
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
        self.updateExecutionState()
    
    def updateInnerDataDebug(self):
        """updateInnerDataDebug(self) -> None
        """
        if not self.DEBUG:
            raise ValueError("This method must be used in a debug mode.")
        self.initInnerData()
        if self._N_ema1 != int(self.le_ema1.text()) or self._N_ema2 != int(self.le_ema2.text()):
            self.setEmaSpan()
        if self._delta != float(self.le_delta.text()):
            self._delta = float(self.le_delta.text())

        start_ = int(self.le_start.text())
        if start_ >= len(self.data):
            raise ValueError('start must be smaller than the length of data.')
        end_ = min([int(self.le_end.text()), len(self.data)])
        data_ = self.data[["open", "high", "low", "close"]].values[start_:end_]
        for ii, row in enumerate(data_):
            buff = np.zeros(5)
            buff[0] = ii + 1
            buff[1:] = row.copy()
            self._timestamp.append(ii + 1)
            self._close.append(row[-1])
            self._ema1.append(self.calcEMA(self._ema1, self._alpha1))
            self._ema2.append(self.calcEMA(self._ema2, self._alpha2))
            self._ohlc_list.append(buff.copy())
            self._cross_signal.append(self.judgeCrossPoint())
            self._extreme_signal.append(self.judgeExtremePoint())
            self.updateExecutionStateDebug()
        
        self.updateResults()
    
    def setEmaSpan(self):
        """setEmaSpan(self) -> None
        set EMA spans
        """
        self._N_ema1 = int(self.le_ema1.text())
        self._N_ema2 = int(self.le_ema2.text())
        self.updateAlpha()
    
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
        if self._look_for_max and diff < self._current_max - self._delta:
            self._look_for_max = False
            self._current_min = diff
            return 1.
        elif (not self._look_for_max) and diff > self._current_min + self._delta:
            self._look_for_max = True
            self._current_max = diff
            return -1.
        else:
            return 0.
    
    def updateExecutionState(self):
        """updateExecutionState(self) -> None
        update the state of execution
        """
        pass

    def updateExecutionStateDebug(self):
        """updateExecutionStateDebug(self) -> None
        update the state of execution in debug mode
        """
        if len(self._close) == 1:
            self._jpy_list.append(0)
            return
        self._jpy_list.append(self._jpy_list[-1])
        if self._current_state == "ask":
            if self._stop_by_cross: # when the previous state is "buy" 
                ltp_ = max([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])
                self._jpy_list[-1] += - (ltp_ - self._order_ltp)
            #     self._jpy_list.append(self._jpy_list[-1] - (ltp_ - self._order_ltp))
            # else:
            #     self._jpy_list.append(self._jpy_list[-1])
            self._order_ltp = max([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])    
            self._current_state = "sell"
        elif self._current_state == "bid":
            if self._stop_by_cross: # when the previous state is "sell" 
                ltp_ = min([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])
                self._jpy_list[-1] += ltp_ - self._order_ltp
            #     self._jpy_list.append(self._jpy_list[-1] + ltp_ - self._order_ltp)
            # else:
            #     self._jpy_list.append(self._jpy_list[-1])
            self._order_ltp = min([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])
            self._current_state = "buy"
        elif self._current_state == "sell":
            if self._extreme_signal[-2] == 1.:
                ltp_ = min([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])
                self._jpy_list[-1] += ltp_ - self._order_ltp
                # self._jpy_list.append(self._jpy_list[-1] + ltp_ - self._order_ltp)
                self._order_ltp = 0
                self._current_state = "wait"
                self._look_for_max = None
            # else:
            #     self._jpy_list.append(self._jpy_list[-1])
        elif self._current_state == "buy":
            if self._extreme_signal[-2] == -1.:
                ltp_ = max([self._ohlc_list[-1][1], self._ohlc_list[-1][-1]])
                self._jpy_list[-1] += - (ltp_ - self._order_ltp)
                # self._jpy_list.append(self._jpy_list[-1] - (ltp_ - self._order_ltp))
                self._order_ltp = 0
                self._current_state = "wait"
                self._look_for_max = None
        #     else:
        #         self._jpy_list.append(self._jpy_list[-1])
        # else:
        #     self._jpy_list.append(self._jpy_list[-1])
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
    
    def updateResults(self):
        """updateResults(self) -> None
        update the results of trades
        """
        self.label_benefit_value.setText(str(self._jpy_list[-1]))
        days = len(self._jpy_list) / 1440.
        self.label_perday_value.setText("{0:.2f}".format(float(self._jpy_list[-1]) / days))
    
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
        self.chart_signal.clear()
        self.chart_signal.plot(
            np.arange(1, len(self._timestamp) + 1), self._cross_signal,
            clear=False, pen=pg.mkPen(self._color_cross_signal, width=2)
        )
        self.chart_signal.plot(
            np.arange(1, len(self._timestamp) + 1), self._extreme_signal,
            clear=False, pen=pg.mkPen(self._color_extreme_signal, width=2)
        )
        self.chart_stock.clear()
        self.chart_stock.plot(
            np.arange(1, len(self._timestamp) + 1), self._jpy_list,
            clear=False, pen=pg.mkPen(self._color_stock, width=2)
        )
    
    def getOHLC(self):
        pass
        # result = get_rate_via_crypto(self._histoticks, self._params_cryptocomp)
        # self.data = to_dataFrame(result, True)
        # print(self.data["time"].values[-1])
        # self.update(None)

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

def main(debug):
    app = QApplication([])
    # app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "python.png")))
    mw = ChartWindow(debug)
    # data = [  ## fields are (time, open, close, min, max).
    #     (1., 10, 15, 5, 13),
    #     (2., 13, 20, 9, 17),
    #     (3., 17, 23, 11, 14),
    #     (4., 14, 19, 5, 15),
    #     (5., 15, 22, 8, 9),
    #     (6., 9, 16, 8, 15),
    # ]
    # fpath = r'..\data\OHLC_20181211.csv'
    file_list = [
        "../data/ohlcv/OHLCV_201901010000_to_201901070000.csv",
        "../data/ohlcv/OHLCV_201901070001_to_201901080000.csv",
        "../data/ohlcv/OHLCV_201901080001_to_201901090000.csv",
    ]

    data = None
    for fpath in file_list:
        if data is None:
            data = pd.read_csv(fpath, index_col=0)
        else:
            data = pd.concat((data, pd.read_csv(fpath, index_col=0)))
    mw.setData(data)
    mw.show()
    app.exec_()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChartWindow")
    parser.add_argument('-debug', action='store', dest='debug', type=str, default="True")
    argmnt = parser.parse_args()
    if argmnt.debug == "True":
        main(True)
    elif argmnt.debug == "False":
        main(False)
    else:
        raise ValueError("option 'debug' must be True or False.")
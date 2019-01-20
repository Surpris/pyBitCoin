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
import pandas as pd
from PyQt5.QtWidgets import QMainWindow, QDialog, QGridLayout, QWidget, QLabel, QLineEdit
from PyQt5.QtWidgets import QApplication, QCheckBox
from PyQt5.QtGui import QPainter, QPalette, QColor
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtCore import Qt, QThread, pyqtSlot
import pyqtgraph as pg
import sys
sys.path.append("../")
import time

try:
    from CustomGraphicsItem import CandlestickItem
except ImportError:
    from .CustomGraphicsItem import CandlestickItem

from utils import make_groupbox_and_grid, make_pushbutton, make_label, calc_EMA
from utils import get_rate_via_crypto, to_dataFrame
from utils import analyze
from utils import DataAdapter

from workers import AnalysisWorker

class ChartWindow(QDialog):
    """ChartWindow class
    This class offers an window to draw candlesticks on.
    """

    def __init__(self, df=None, debug=False, *args):
        """__init__(self, *args) -> None
        initialize this class
        """
        super().__init__(*args)

        self.initInnerParameters(df, debug)
        self.initAnalysisThread()
        self.initGui()
    
    def initInnerParameters(self, df, debug):
        """initInnerParameters(self, debug) -> None
        initialize the inner parameters

        Parameters
        ----------
        debug : bool
        """

        # for GUI
        self._window_width = 720 # [pixel]
        self._window_height = 720 # [pixel]
        self._spacing = 5 # [pixel]
        self._groupbox_title_font_size = 14
        self._label_font_size = 14
        self._window_color = "gray"
        self._txt_bg_color = "#D0D3D4"
        self._chk_box_bg_color = "#FFFFFF"

        # for settings
        self._N_ema_min = 10
        self._N_ema_max = 15
        self._btc_volime = 1.
        self._count = 0
        self._N_ema1 = 20
        self._N_ema2 = 21
        self._delta = 10. # for judgement of extreme maxima / minima
        self._datetimeFmt_BITFLYER = "%Y-%m-%dT%H:%M:%S.%f"
        self._datetimeFmt_BITFLYER_2 = "%Y-%m-%dT%H:%M:%S"
        self._N_benefit = 5
        self._N_dec = 5

        # set DataAdapter
        self._adapter = DataAdapter(df=df, 
            N_ema_max=self._N_ema_max, N_ema_min=self._N_ema_min,
            N_dec=self._N_dec, N_ema1=self._N_ema1, N_ema2=self._N_ema2,
            delta=self._delta, 
        )

        # for chart
        self._color_ema1 = "#3C8CE7"
        self._color_ema2 = "#EE8F1D"
        self._color_cross_signal = "#FFFFFF"
        self._color_extreme_signal = "#E8EE1D"
        self._color_stock = "#FFFFFF"

        self._color_stat = "#2FC4DF"

        # for CryptoCompare
        # self._histoticks = "minute"
        # self._limit = int(4*60 - 1)
        # self.setCryptoCompareParam()
        
        # for inner data
        self.initInnerData()

        # for DEBUG
        self.DEBUG = debug
        self.data = df
    
    # def setCryptoCompareParam(self):
    #     """setCryptoCompareParam(self) -> None
    #     """
    #     self._params_cryptocomp = {
    #         "fsym": "BTC",
    #         "tsym": "JPY",
    #         "limit": str(self._limit),
    #         "e": "bitFlyerfx",
    #     }
    
    def initInnerData(self):
        """initInnerData(self) -> None
        initialize the inner data
        """
        self.initOHLCVData()
        self.initAnalysisData()

    def initOHLCVData(self):
        """initOHLCVData(self) -> None
        intialize the inner data related to charts of OHLCV
        """
        self._timestamp = []
        self._latest = None
        self._tmp_ltp = []
        self._tmp_ohlc = []
        self._ltp = []
        self._ohlc_list = []
        self._volume_list = []
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
    
    def initAnalysisData(self):
        """initAnalysisData(self) -> None
        initialize the inner data related to analysis
        """
        self._benefit_map = np.zeros((self._N_ema_max + 1, self._N_ema_max + 1), dtype=int)
        self._results_list = []
        # self._cross_points_list = []
        # self._stat_dead_list = []
        # self._stat_golden_list = []
        # self._ext_dead_list = []
        # self._ext_golden_list = []
    
    def initAnalysisThread(self):
        self._thread_analysis = QThread()
        self._worker_analysis = AnalysisWorker(
            N_ema_max=self._N_ema_max, N_ema_min=self._N_ema_min, 
            N_dec=self._N_dec
        )
        self._worker_analysis.do_something.connect(self.updateAnalysisResults)
        self._worker_analysis.moveToThread(self._thread_analysis)

        # start
        self._thread_analysis.started.connect(self._worker_analysis.process)

        # finished
        self._worker_analysis.finished.connect(self._thread_analysis.quit)
        # self._thread_analysis.finished.connect(self.checkIsTimerStopped)
    
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
        
        # plots and charts
        self.glw = pg.GraphicsLayoutWidget()

        ## benefit map
        self.plot_benefit = self.glw.addPlot(
            # axisItems={"bottom":self.iw_axBottom, "left":self.iw_axLeft}
        )
        self.plot_benefit.setAspectLocked(True)
        # self.plot_benefit.setMaximumWidth(100)
        self.img_benefit = pg.ImageItem()
        self.plot_benefit.addItem(self.img_benefit)

        # self.label_coor_value = make_label(
        #     group_analysis, "(NA,NA)", self._label_font_size, True, Qt.AlignLeft
        # )

        def mouseMoved(pos):
            try:
                coor = self.img_benefit.mapFromScene(pos)
                x, y = int(coor.x()), int(coor.y())
                if self.img_benefit.image is not None:
                    img = self.img_benefit.image
                    if 0 <= x <= img.shape[1] and 0 <= y <= img.shape[0]:
                        pass
                        # self.label_coor_value.setText("({0}, {1}, {2:.2e})".format(x, y, img[y, x]))
            except Exception as ex:
                print(ex)
        
        self.img_benefit.scene().sigMouseMoved.connect(mouseMoved)

        ## OHLC chart
        self.chart_ohlc = self.glw.addPlot()

        self.glw.nextRow()

        ## Box plot diagram for dead cross
        self.plot_box_dead = self.glw.addPlot()
        # self.plot_box_dead.setMaximumWidth(100)

        ## volume chart
        self.chart_volume = self.glw.addPlot()
        # self.chart_volume.setMaximumHeight(self._window_height // 6)

        self.glw.nextRow()

        ## Box plot diagram for golden cross
        self.plot_box_golden = self.glw.addPlot()
        # self.plot_box_golden.setMaximumWidth(100)

        ## signal chart
        self.chart_signal = self.glw.addPlot()
        # self.chart_signal.setMaximumHeight(self._window_height // 6)

        self.glw.nextRow()
        _ = self.glw.addPlot()

        ## stock chart
        self.chart_stock = self.glw.addPlot()
        # self.chart_stock.setMaximumHeight(self._window_height // 6)

        # Settings
        group_setting, grid_setting = make_groupbox_and_grid(
            self, 40, (self._window_height) // 3,
            "Settings", self._groupbox_title_font_size, self._spacing
        )

        label_ema1 = make_label(
            group_setting, "N1", self._label_font_size, True, Qt.AlignLeft
        )
        grid_setting.addWidget(label_ema1, 0, 0)

        self.le_ema1 = QLineEdit(group_setting)
        self.le_ema1.setText(str(self._N_ema1))
        # font = self.le_ema1.font()
        # font.setPointSize(self._button_font_size)
        # self.le_ema1.setFont(font)
        self.le_ema1.setMaximumWidth(40)
        self.le_ema1.setMaximumHeight(16)
        # self.le_ema1.resize(20, 16)
        self.le_ema1.setStyleSheet("background-color:{};".format(self._txt_bg_color))
        self.le_ema1.setValidator(QIntValidator())
        grid_setting.addWidget(self.le_ema1, 0, 1)

        label_ema2 = make_label(
            group_setting, "N2", self._label_font_size, True, Qt.AlignLeft
        )
        grid_setting.addWidget(label_ema2, 1, 0)

        self.le_ema2 = QLineEdit(group_setting)
        self.le_ema2.setText(str(self._N_ema2))
        # font = self.le_ema2.font()
        # font.setPointSize(self._button_font_size)
        # self.le_ema2.setFont(font)
        self.le_ema2.setMaximumWidth(40)
        self.le_ema2.setMaximumHeight(16)
        # self.le_ema2.resize(20, 16)
        self.le_ema2.setStyleSheet("background-color:{};".format(self._txt_bg_color))
        self.le_ema2.setValidator(QIntValidator())
        grid_setting.addWidget(self.le_ema2, 1, 1)

        label_delta = make_label(
            group_setting, "delta", self._label_font_size, True, Qt.AlignLeft
        )
        grid_setting.addWidget(label_delta, 2, 0)

        self.le_delta = QLineEdit(group_setting)
        self.le_delta.setText(str(self._delta))
        # font = self.le_delta.font()
        # font.setPointSize(self._button_font_size)
        # self.le_delta.setFont(font)
        self.le_delta.setMaximumWidth(40)
        self.le_delta.setMaximumHeight(16)
        self.le_delta.setStyleSheet("background-color:{};".format(self._txt_bg_color))
        self.le_delta.setValidator(QDoubleValidator())
        grid_setting.addWidget(self.le_delta, 2, 1)

        # Results
        group_results, grid_results = make_groupbox_and_grid(
            self, 40, (self._window_height) // 3,
            "Results", self._groupbox_title_font_size, self._spacing
        )
        label_benefit = make_label(
            group_results, "Benefit", self._label_font_size, True, Qt.AlignLeft
        )
        self.label_benefit_value = make_label(
            group_results, "0", self._label_font_size, True, Qt.AlignLeft
        )
        label_perday = make_label(
            group_results, "Per day", self._label_font_size, True, Qt.AlignLeft
        )
        self.label_perday_value = make_label(
            group_results, "0", self._label_font_size, True, Qt.AlignLeft
        )

        grid_results.addWidget(label_benefit, 0, 0)
        grid_results.addWidget(self.label_benefit_value, 1, 0)
        grid_results.addWidget(label_perday, 2, 0)
        grid_results.addWidget(self.label_perday_value, 3, 0)

        self.grid.addWidget(self.glw, 0, 0, 3, 5)
        self.grid.addWidget(group_setting, 0, 5, 1, 1)
        self.grid.addWidget(group_results, 1, 5, 1, 1)

        # Items in debug mode
        if self.DEBUG:
            group_debug, grid_debug = make_groupbox_and_grid(
                self, 60, self._window_height // 3,
                "DEBUG", self._groupbox_title_font_size, self._spacing
            )

            ## start position
            self.le_start = QLineEdit(group_debug)
            self.le_start.setText("0")
            # font = self.le_start.font()
            # font.setPointSize(self._button_font_size)
            # self.le_start.setFont(font)
            self.le_start.resize(40, 16)
            self.le_start.setStyleSheet("background-color:{};".format(self._txt_bg_color))
            self.le_start.setValidator(QIntValidator())

            ## end position
            self.le_end = QLineEdit(group_debug)
            self.le_end.setText("100")
            self.le_end.resize(40, 16)
            self.le_end.setStyleSheet("background-color:{};".format(self._txt_bg_color))
            self.le_end.setValidator(QIntValidator())

            ## checkbox to use the average values of each OHLC as order ltps
            self.chk_use_average = QCheckBox(group_debug)
            pal = QPalette()
            pal.setColor(QPalette.Foreground, QColor(self._chk_box_bg_color))
            # pal.setColor(QPalette.Active, QColor("white"))
            self.chk_use_average.setPalette(pal)
            # self.chk_use_average.setStyleSheet("background-color:{};".format(self._chk_bg_color))
            self.chk_use_average.setChecked(False)
            self.chk_use_average.resize(16, 16)
            # self.chk_use_average.stateChanged.connect(self.setTxtBTCJPYEditState)

            ## update button
            self.button1 = make_pushbutton(
                self, 40, 16, "Update", 14, 
                method=self.update, color=None, isBold=False
            )

            ## button to get OHLCV data from CryptoCompare
            # self.button2 = make_pushbutton(
            #     self, 40, 16, "Get OHLC", 14, 
            #     method=self.getOHLC, color=None, isBold=False
            # )

            self.button3 = make_pushbutton(
                self, 40, 16, "Analyze", 14, 
                method=self.analyze, color=None, isBold=False
            )

            self.button4 = make_pushbutton(
                self, 40, 16, "View", 14, 
                method=self.drawAnalysisResults, color=None, isBold=False
            )

            ## add
            grid_debug.addWidget(self.le_start, 0, 0)
            grid_debug.addWidget(self.le_end, 1, 0)
            grid_debug.addWidget(self.chk_use_average, 2, 0)
            grid_debug.addWidget(self.button1, 3, 0)
            grid_debug.addWidget(self.button3, 4, 0)
            grid_debug.addWidget(self.button4, 5, 0)

            self.grid.addWidget(group_debug, 2, 5, 1, 1)
    
    def initMainGrid(self):
        """ initMainWidget(self) -> None
        initialize the main widget and its grid.
        """
        self.resize(self._window_width, self._window_height)
        self.setStyleSheet("background-color:{};".format(self._window_color))
        self.grid = QGridLayout(self)
        self.grid.setSpacing(5)
    
    @pyqtSlot()
    def update(self):
        """update(self) -> None
        update the inner adapter and graphs
        """
        try:
            self.updateInnerAdapter()
            self.updatePlots()
        except Exception as ex:
            _, _2, exc_tb = sys.exc_info()
            # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("line {}: {}".format(exc_tb.tb_lineno, ex))
    
    def updateInnerAdapter(self):
        if self._adapter.N_ema1 != int(self.le_ema1.text()) or self._N_ema2 != int(self.le_ema2.text()):
            self._adapter.N_ema1 = int(self.le_ema1.text())
            self._adapter.N_ema2 = int(self.le_ema2.text())
        if self._adapter.delta != float(self.le_delta.text()):
            self._adapter.delta = float(self.le_delta.text())
        
        # if need_update:
        self._adapter.initOHLCVData()
        self.updateResults()
    
    def updateResults(self):
        """updateResults(self) -> None
        update the results of trades
        """
        self.label_benefit_value.setText(str(self._adapter.jpy_list[-1]))
        days = len(self._adapter.jpy_list) / 1440.
        self.label_perday_value.setText("{0:.2f}".format(float(self._adapter.jpy_list[-1]) / days))
    
    def updatePlots(self):
        """updatePlots(self) -> None
        update Grpahs
        """
        start_ = int(self.le_start.text())
        if start_ >= len(self._adapter.data):
            raise ValueError('start must be smaller than the length of data.')
        end_ = min([int(self.le_end.text()), len(self._adapter.data)])

        self.chart_ohlc.clear()
        self.chart_ohlc.addItem(CandlestickItem(self._adapter.ohlc_list[start_:end_]))
        self.chart_ohlc.plot(
            np.arange(1, len(self._adapter.timestamp[start_:end_]) + 1), 
            self._adapter.ema1[start_:end_], 
            clear=False, pen=pg.mkPen(self._color_ema1, width=2)
        )
        self.chart_ohlc.plot(
            np.arange(1, len(self._adapter.timestamp[start_:end_]) + 1), 
            self._adapter.ema2[start_:end_], 
            clear=False, pen=pg.mkPen(self._color_ema2, width=2)
        )
        
        self.chart_volume.clear()
        self.chart_volume.plot(
            np.arange(1, len(self._adapter.timestamp[start_:end_]) + 1), 
            self._adapter.volume_list[start_:end_],
            clear=False, pen=pg.mkPen("#FFFFFF", width=2)
        )

        self.chart_signal.clear()
        self.chart_signal.plot(
            np.arange(1, len(self._adapter.timestamp[start_:end_]) + 1), 
            self._adapter.cross_signal[start_:end_],
            clear=False, pen=pg.mkPen(self._color_cross_signal, width=2)
        )
        self.chart_signal.plot(
            np.arange(1, len(self._adapter.timestamp[start_:end_]) + 1), 
            self._adapter.extreme_signal[start_:end_],
            clear=False, pen=pg.mkPen(self._color_extreme_signal, width=2)
        )

        self.chart_stock.clear()
        self.chart_stock.plot(
            np.arange(1, len(self._adapter.timestamp[start_:end_]) + 1), 
            self._adapter.jpy_list[start_:end_],
            clear=False, pen=pg.mkPen(self._color_stock, width=2)
        )
    
    @pyqtSlot()
    def analyze(self):
        """analyze(self) -> None
        analyze OHLC dataset
        """
        if not self._thread_analysis.isRunning():
            if self.DEBUG:
                print("start thread.")
            self._worker_analysis.dataset = self.data.copy()
            self._worker_analysis.delta = self._delta
            self._thread_analysis.start()
        else:
            if self.DEBUG:
                print("Thread is running.")
    
    def updateAnalysisResults(self, data):
        """updateAnalysisResults(self, data) -> None
        update the results of analysis

        Parameters
        ----------
        data : dict
            'data' has the following key-value pairs.
            benefit_map     : numpy.2darray
            results_list    : list of dict object
            # stat_dead       : list of numpy.2darray
            # stat_golden     : list of numpy.2darray
            # ext_dead_list   : list of list with numpy.2darray
            # ext_golden_list : list of list with numpy.2darray
        """
        try:
            self._benefit_map = data["benefit_map"]
            self._results_list = data["results_list"]
            # self._cross_points_list = data["cross_points_list"]
            # self._stat_dead_list = data["stat_dead_list"]
            # self._stat_golden_list = data["stat_golden_list"]
            # self._ext_dead_list = data["ext_dead_list"]
            # self._ext_golden_list = data["ext_golden_list"]
            self.drawAnalysisResults()
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("line {}:{}".format(exc_tb.tb_lineno, ex))

    @pyqtSlot()
    def drawAnalysisResults(self):
        """drawAnalysisResults(self) -> None
        draw the results of analysis
        """
        self.img_benefit.setImage(self._benefit_map)

        ii = self._N_ema1 - self._N_ema_min
        if ii < 0:
            print("N1 must be >= {0}.".format(self._N_ema_min))
            return
        results = self._results_list[ii]

        self.plot_box_dead.clear()
        self.plot_box_dead.plot(
            np.arange(2**self._N_dec), results["stat_dead"][:, 2],
            clear=False, pen=pg.mkPen(self._color_stat, width=2)
        )

        self.plot_box_golden.clear()
        self.plot_box_golden.plot(
            np.arange(2**self._N_dec), results["stat_golden"][:, 2],
            clear=False, pen=pg.mkPen(self._color_stat, width=2)
        )

        if len(self._timestamp) == 0:
            self.update()
        else:
            self.updatePlots()
        
        # self.chart_ohlc.plot(
        #     np.arange(1, len(self._timestamp) + 1), results["ema1"][:len(self._timestamp)],
        #     clear=False, pen=pg.mkPen("#3DD73F", width=2)
        # )
        # self.chart_ohlc.plot(
        #     np.arange(1, len(self._timestamp) + 1), results["ema2"][:len(self._timestamp)],
        #     clear=False, pen=pg.mkPen("#E745EC", width=2)
        # )

        self.chart_volume.clear()
        self.chart_volume.plot(
            np.arange(1, len(self._timestamp) + 1), np.array(self._ema1) - np.array(self._ema2),
            clear=False, pen=pg.mkPen(self._color_cross_signal, width=2)
        )

        self.chart_stock.clear()
        self.chart_stock.plot(
            np.arange(1, len(self._timestamp) + 1), results["cross_points"][:len(self._timestamp)],
            clear=False, pen=pg.mkPen(self._color_cross_signal, width=2)
        )
        position_ext = results["position_ext"]
        a_k = results["a_k"]
        position_plot = np.zeros(len(self._timestamp))
        count = 0
        for ii in range(len(self._timestamp)):
            if ii == position_ext[count]:
                position_plot[ii] = a_k[count][1]
                count += 1
        self.chart_stock.plot(
            np.arange(1, len(self._timestamp) + 1), position_plot,
            clear=False, pen=pg.mkPen(self._color_extreme_signal, width=2)
        )
        
    
    def setData(self, data):
        """setData(self, data) -> None
        set data
        """
        if not self.DEBUG:
            raise ValueError("This method is valid only in debug mode.")
        self._adapter.data = data
        self.data = data
        self._count = 0

def main():
    import glob
    file_list = glob.glob("../data/ohlcv/OHLCV*.csv")
    data = None
    for fpath in file_list:
        print(fpath)
        if data is None:
            data = pd.read_csv(fpath, index_col=0)
        else:
            data = pd.concat((data, pd.read_csv(fpath, index_col=0)))
    app = QApplication([])
    mw = ChartWindow(data, True)
    # mw.setData(data)
    mw.show()
    app.exec_()

if __name__ == "__main__":
    main()
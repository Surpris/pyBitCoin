# -*- coding: utf-8 -*-

import sys
import inspect
import time
import os
import json
import datetime
from collections import OrderedDict
import glob
import pybitflyer

from PyQt5.QtWidgets import QMainWindow, QGridLayout, QMenu, QWidget, QLabel, QLineEdit
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtGui import QIcon, QPalette, QColor, QPixmap
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QPushButton, QMessageBox, QGroupBox, QDialog, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QStyle
from PyQt5.QtCore import pyqtSlot, QThread, QTimer, Qt, QMutex
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg

from utils.decorator import footprint
from Worker import GetTickerWorker

class OrderBoard(QMainWindow):
    """OrderBoard class
    """
    
    def __init__(self, filepath=""):
        super().__init__()
        self.initInnerParameters(filepath)
        self.initGui()
        self.initGetDataProcess()
    
    @footprint
    def initInnerParameters(self, filepath):
        """
        Initialize the inner parameters.
        """
        self._mutex = QMutex()
        # self._windows = []
        self.initData()
        self._font_size_button = 16 # [pixel]
        self._font_size_groupbox_title = 12 # [pixel]
        self._font_size_label = 11 # [pixel]
        self._font_bold_label = True
        self._init_window_width = 333 # [pixel]
        self._init_window_height = 592 # [pixel]
        self._init_button_color = "#EBF5FB"
        self.main_bgcolor = "#FDF2E9"

        self._get_data_interval = 1 # [sec]
        self._get_data_worker_sleep_interval = self._get_data_interval - 0.1 # [sec]

        self._currentDir = os.path.dirname(__file__)
        self._closing_dialog = True

        self._product_code = "FX_BTC_JPY"
        self._api_dir = ".prv"
        # fldrname_for_key = getpass.getpass("folder for key:")
        fpath = glob.glob(os.path.join(os.environ["USERPROFILE"], self._api_dir, "*"))[0]

        with open(fpath, "r", encoding="utf-8") as ff:
            try:
                self._api_key = ff.readline().strip()
                self._api_secret = ff.readline().strip()
            except Exception as ex:
                print(ex)
        
        self._api = pybitflyer.API(api_key=self._api_key, api_secret=self._api_secret)
        try:
            _ = self._api.ticker(product_code=self._product_code)
        except Exception as ex:
            print(ex)

        # if os.path.exists(os.path.join(os.path.dirname(__file__), "config.json")):
        #     self.loadConfig()
        # if os.path.exists(filepath):
        #     self.loadConfigGetData(filepath)
    
    @footprint
    @pyqtSlot()
    def initData(self):
        """ initData(self) -> None
        Initialize inner data.
        """
        self._executions = []

######################## Construction of GUI ########################
    @footprint
    def initMainWidget(self):
        """ initMainWidget(self) -> None
        Initialize the main widget and the grid.
        """
        self.main_widget = QWidget(self)
        self.setStyleSheet("background-color:{};".format(self.main_bgcolor))
        self.grid = QGridLayout(self.main_widget)
        self.grid.setSpacing(10)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "python.png")))
    
    @footprint
    def initGui(self):
        """
        Initialize the GUI.
        """
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.initMainWidget()
        # self.setMenuBar()

        self.setWindowTitle("Order Board")
        self.resize(self._init_window_width, self._init_window_height)

        """ Board information """
        group_boardinfo, grid_boardinfo = \
            self.__makeGroupboxAndGrid(self, self._init_window_width - 20, 50, 
                                       "Board Info.", self._font_size_groupbox_title, 10)

        # Best ask
        label_best_ask = self.__makeLabel(group_boardinfo, "Best Ask: ", self._font_size_label, 
                                     isBold=self._font_bold_label, alignment=Qt.AlignRight)
        
        self.label_best_ask_value = \
            self.__makeLabel(group_boardinfo, "-1", self._font_size_label, 
                             isBold=self._font_bold_label, alignment=Qt.AlignLeft, color="green")

        # Last execution
        label_ltp = self.__makeLabel(group_boardinfo, "Last Trade: ", self._font_size_label, 
                                     isBold=self._font_bold_label, alignment=Qt.AlignRight)
        
        self.label_ltp_value = \
            self.__makeLabel(group_boardinfo, "-1", self._font_size_label, 
                             isBold=self._font_bold_label, alignment=Qt.AlignLeft, color="#0B5345")

        # Best bid
        label_best_bid = self.__makeLabel(group_boardinfo, "Best Bid: ", self._font_size_label, 
                                     isBold=self._font_bold_label, alignment=Qt.AlignRight)
        
        self.label_best_bid_value = \
            self.__makeLabel(group_boardinfo, "-1 ", self._font_size_label, 
                             isBold=self._font_bold_label, alignment=Qt.AlignLeft, color="red")
        
        # Start ticker button
        # self.btn_start_ticker = \
        #     self.__makePushButton(group_boardinfo, 
        #                           (self._init_window_width - 40)//4, 60, 
        #                           "Start", self._font_size_button, self.getTickerManually, 
        #                           color=self._init_button_color)
        self.btn_start_ticker = \
            self.__makePushButton(group_boardinfo, 
                                  (self._init_window_width - 40)//4, 60, 
                                  "Start", self._font_size_button, self.runAutoGetTicker, 
                                  color=self._init_button_color)

        # construct the layout
        grid_boardinfo.addWidget(label_best_ask, 0, 0, 1, 1)
        grid_boardinfo.addWidget(self.label_best_ask_value, 0, 1, 1, 1)

        grid_boardinfo.addWidget(label_ltp, 1, 0, 1, 1)
        grid_boardinfo.addWidget(self.label_ltp_value, 1, 1, 1, 1)

        grid_boardinfo.addWidget(label_best_bid, 2, 0, 1, 1)
        grid_boardinfo.addWidget(self.label_best_bid_value, 2, 1, 1, 1)

        grid_boardinfo.addWidget(self.btn_start_ticker, 0, 2, 3, 1)

        """ Bid / Ask setting """
        group_bidask, grid_bidask = \
            self.__makeGroupboxAndGrid(self, self._init_window_width - 20, 30, 
                                       "Start from", self._font_size_groupbox_title, 10)
        
        self.btn_ask = self.__makePushButton(group_bidask, (self._init_window_width - 40)//2, 20, 
                                             "Ask", self._font_size_button, None, 
                                             color="green")
        self.btn_ask.setCheckable(True)
        self.btn_ask.clicked.connect(self.updateOnAsk)
        
        self.btn_bid = self.__makePushButton(group_bidask, (self._init_window_width - 40)//2, 20, 
                                             "Bid", self._font_size_button, None, 
                                             color="red")
        self.btn_bid.setCheckable(True)
        self.btn_bid.clicked.connect(self.updateOnBid)

        # construct the layout
        grid_bidask.addWidget(self.btn_ask, 0, 0)
        grid_bidask.addWidget(self.btn_bid, 0, 1)

        """ Volume buttons """
        group_volume, grid_volume = \
            self.__makeGroupboxAndGrid(self, self._init_window_width - 20, 30, 
                                       "Volume (BTC)", self._font_size_groupbox_title, 10)

        # +0.01 BTCs button
        self.btn_1pct = self.__makePushButton(group_volume, 
                                               (self._init_window_width - 40)//4, 20, 
                                               "+0.01", self._font_size_button, self.add1pct, 
                                               color=self._init_button_color)

        # +0.1 BTCs button
        self.btn_10pct = self.__makePushButton(group_volume, 
                                               (self._init_window_width - 40)//4, 20, 
                                               "+0.1", self._font_size_button, self.add10pct, 
                                               color=self._init_button_color)

        # +1 BTCs button
        self.btn_100pct = self.__makePushButton(group_volume, 
                                               (self._init_window_width - 40)//4, 20, 
                                               "+1", self._font_size_button, self.add100pct, 
                                               color=self._init_button_color)

        # clear button
        self.btn_clear = self.__makePushButton(group_volume, 
                                               (self._init_window_width - 40)//4, 20, 
                                               "C", self._font_size_button, self.clearVolume, 
                                               color=self._init_button_color)

        # construct the layout
        grid_volume.addWidget(self.btn_1pct, 0, 0)
        grid_volume.addWidget(self.btn_10pct, 0, 1)
        grid_volume.addWidget(self.btn_100pct, 0, 2)
        grid_volume.addWidget(self.btn_clear, 0, 3)

        """ Value setting """
        group_values, grid_values = \
            self.__makeGroupboxAndGrid(self, self._init_window_width - 20, 50, 
                                       "Values", self._font_size_groupbox_title, 10)
        
        # BTC volume
        self.txt_btc = QLineEdit(group_values)
        self.txt_btc.setText("0")
        font = self.txt_btc.font()
        font.setPointSize(self._font_size_button)
        self.txt_btc.setFont(font)
        self.txt_btc.resize((self._init_window_width - 40)//2, 20)
        self.txt_btc.setStyleSheet("background-color:{};".format("white"))
        self.txt_btc.setValidator(QDoubleValidator())
        self.txt_btc.textChanged.connect(self.updateExpectedValues)

        label_btc_volume = self.__makeLabel(group_values, "BTC", self._font_size_label, 
                                            isBold=self._font_bold_label, alignment=Qt.AlignLeft)
        
        # BTCJPY
        ## Auto-manual flag checkbox
        self.chk_btcjpy = QCheckBox(group_values)
        self.chk_btcjpy.setChecked(True)
        self.chk_btcjpy.resize(20, 20)
        # self.chk_btcjpy.stateChanged.connect()

        ## TextBox
        self.txt_btcjpy = QLineEdit(group_values)
        self.txt_btcjpy.setText("0")
        font = self.txt_btcjpy.font()
        font.setPointSize(self._font_size_button)
        self.txt_btcjpy.setFont(font)
        self.txt_btcjpy.resize((self._init_window_width - 40)//2, 20)
        self.txt_btcjpy.setStyleSheet("background-color:{};".format("white"))
        self.txt_btcjpy.setValidator(QIntValidator())
        self.txt_btcjpy.textChanged.connect(self.updateExpectedValues)

        label_jpy_unit = self.__makeLabel(group_values, "yen", self._font_size_label, 
                                          isBold=self._font_bold_label, alignment=Qt.AlignLeft)
        
        # Stop value (relative)
        label_stop = self.__makeLabel(group_values, "Stop: ", self._font_size_label, 
                                      isBold=self._font_bold_label, alignment=Qt.AlignLeft)
        
        self.txt_stop = QLineEdit(group_values)
        self.txt_stop.setText("0")
        font = self.txt_stop.font()
        font.setPointSize(self._font_size_button)
        self.txt_stop.setFont(font)
        self.txt_stop.resize((self._init_window_width - 40)//2, 20)
        self.txt_stop.setStyleSheet("background-color:{};".format("white"))
        self.txt_stop.setValidator(QIntValidator())
        self.txt_stop.textChanged.connect(self.updateExpectedStop)

        label_stop_unit = self.__makeLabel(group_values, "yen", self._font_size_label, 
                                           isBold=self._font_bold_label, alignment=Qt.AlignLeft)

        # Goal value (relative)
        label_goal = self.__makeLabel(group_values, "Goal: ", self._font_size_label, 
                                     isBold=self._font_bold_label, alignment=Qt.AlignLeft)
        
        self.txt_goal = QLineEdit(group_values)
        self.txt_goal.setText("0")
        font = self.txt_goal.font()
        font.setPointSize(self._font_size_button)
        self.txt_goal.setFont(font)
        self.txt_goal.resize((self._init_window_width - 40)//2, 24)
        self.txt_goal.setStyleSheet("background-color:{};".format("white"))
        self.txt_goal.setValidator(QIntValidator())
        self.txt_goal.textChanged.connect(self.updateExpectedGoal)

        label_goal_unit = self.__makeLabel(group_values, "yen", self._font_size_label, 
                                           isBold=self._font_bold_label, alignment=Qt.AlignLeft)

        # construct the layout
        grid_values.addWidget(self.txt_btc, 0, 1)
        grid_values.addWidget(label_btc_volume, 0, 2)
        
        grid_values.addWidget(self.chk_btcjpy, 1, 0)
        grid_values.addWidget(self.txt_btcjpy, 1, 1)
        grid_values.addWidget(label_jpy_unit, 1, 2)

        grid_values.addWidget(label_stop, 2, 0)
        grid_values.addWidget(self.txt_stop, 2, 1)
        grid_values.addWidget(label_stop_unit, 2, 2)

        grid_values.addWidget(label_goal, 3, 0)
        grid_values.addWidget(self.txt_goal, 3, 1)
        grid_values.addWidget(label_goal_unit, 3, 2)
        
        """ Expected values """
        group_expected, grid_expected = \
            self.__makeGroupboxAndGrid(self, self._init_window_width - 20, 50, 
                                       "Expected values", self._font_size_groupbox_title, 10)
        
        # Expected current value
        label_expected_current = self.__makeLabel(group_expected, "Current value: ", self._font_size_label, 
                                                  isBold=self._font_bold_label, alignment=Qt.AlignRight)
        
        self.expected_current = self.__makeLabel(group_expected, "0", self._font_size_label, 
                                                 isBold=self._font_bold_label, alignment=Qt.AlignLeft)

        # Expected stop value
        label_expected_stop = self.__makeLabel(group_expected, "Stop value: ", self._font_size_label, 
                                               isBold=self._font_bold_label, alignment=Qt.AlignRight)
        
        self.expected_stop = self.__makeLabel(group_expected, "0", self._font_size_label, 
                                              isBold=self._font_bold_label, alignment=Qt.AlignLeft)
        
        # Expected goal value
        label_expected_goal = self.__makeLabel(group_expected, "Goal value: ", self._font_size_label, 
                                               isBold=self._font_bold_label, alignment=Qt.AlignRight)
        
        self.expected_goal = self.__makeLabel(group_expected, "0", self._font_size_label, 
                                              isBold=self._font_bold_label, alignment=Qt.AlignLeft)
        
        # construct the layout
        grid_expected.addWidget(label_expected_current, 0, 0)
        grid_expected.addWidget(self.expected_current, 0, 1)
        grid_expected.addWidget(label_expected_stop, 1, 0)
        grid_expected.addWidget(self.expected_stop, 1, 1)
        grid_expected.addWidget(label_expected_goal, 2, 0)
        grid_expected.addWidget(self.expected_goal, 2, 1)

        """ Order button """
        self.btn_order = self.__makePushButton(self, self._init_window_width - 40, 20, 
                                               "Order", self._font_size_button, None, 
                                               color=self._init_button_color)
        self.btn_order.setEnabled(False)

        """ add all the widget """
        self.grid.addWidget(group_boardinfo, 0, 0)
        self.grid.addWidget(group_bidask, 1, 0)
        self.grid.addWidget(group_volume, 2, 0)
        self.grid.addWidget(group_values, 3, 0)
        self.grid.addWidget(group_expected, 4, 0)
        self.grid.addWidget(self.btn_order, 5, 0)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        self.setFixedSize(self.size())
    
    def __makeGroupboxAndGrid(self, parent, width, height, title, fontsize, spacing):
        """__makeGroupboxAndGrid(self, parent, width, height, title, fontsize, spacing) -> groupbox, grid

        Parameters
        ----------
        parent : parent class overtaking QtWidgets
        width : int
        height : int
        title : str
        fontsize : int
        spacing : int

        Returns
        -------
        groupbox : QGroupBox
        grid : QGridLayout
        """

        groupbox = QGroupBox(parent)
        groupbox.setTitle(title)
        font = groupbox.font()
        font.setPointSize(fontsize)
        groupbox.setFont(font)
        groupbox.resize(width, height)
        grid = QGridLayout(groupbox)
        grid.setSpacing(spacing)
        return groupbox, grid
    
    def __makeLabel(self, parent, text, fontsize, isBold=False, alignment=None, color=None):
        """__makeLabel(self, parent, text, fontsize, isBold, alignment, color) -> QLable

        Parameters
        ----------
        parent : parent class overtaking QtWidgets
        text : str
        fontsize : int
        isBold : bool
        alignment : Qt.Align
        color : str (color code)

        Returns
        -------
        label : QLabel
        """

        label = QLabel(parent)
        label.setText(text)
        font = label.font()
        font.setPointSize(fontsize)
        font.setBold(isBold)
        label.setFont(font)
        
        if alignment is not None:
            label.setAlignment(alignment)
        if color is not None:
            pal = QPalette()
            pal.setColor(QPalette.Foreground, QColor(color))
            label.setPalette(pal)
        return label
    
    def __makePushButton(self, parent, width, height, text, fontsize, method=None, color=None):
        """__makePushButton(self, parent, width, height, text, fontsize, method, color=None) -> QPushButton

        Parameters
        ----------
        parent : class overtaking QtWidgets
        width : int
        height : int
        text : str
        fontsize : str
        method : function
        color : str (color code)

        Returns
        -------
        button : QPushButton

        """
        # clear button
        button = QPushButton(parent)
        button.resize(width, height)
        button.setText(text)
        font = button.font()
        font.setPointSize(fontsize)
        button.setFont(font)
        
        if color is not None:
            button.setStyleSheet("background-color:{};".format(color))
        if method is not None:
            button.clicked.connect(method)

        return button

######################## Widgets' functions ########################
    @footprint
    @pyqtSlot()
    def runAutoGetTicker(self):
        if not self._timer_getData.isActive():
            # self.initData()
            self._timer_getData.start()
            self.btn_start_ticker.setText("Stop")
        else:
            self.btn_start_ticker.setEnabled(False)
            self.stopTimer = True

    @footprint
    @pyqtSlot()
    def getTickerMaually(self):
        mag = 100
        try:
            result = self._api.ticker(product_code=self._product_code)
            if "timestamp" not in result.keys():
                print("Failure in getting ticker.")
                return
            self.label_best_ask_value.setText(str(result["best_ask"]))
            self.label_ltp_value.setText(str(result["ltp"]))
            self.label_best_bid_value.setText(str(result["best_bid"]))
            if self.chk_btcjpy.isChecked():
                ltp = int(result["ltp"])
                ltp_to_set = (ltp // mag + 1) * mag
                self.txt_btcjpy.setText(str(ltp_to_set))
        except Exception as ex:
            print(ex)
            return

    @footprint
    @pyqtSlot()
    def updateOnAsk(self):
        self.btn_bid.setChecked(False)
        self.validateOrder()
        self.updateExpectedStop()
        self.updateExpectedGoal()
    
    @footprint
    @pyqtSlot()
    def updateOnBid(self):
        self.btn_ask.setChecked(False)
        self.validateOrder()
        self.updateExpectedStop()
        self.updateExpectedGoal()
    
    @footprint
    @pyqtSlot()
    def validateOrder(self):
        if not self.btn_ask.isChecked() and not self.btn_bid.isChecked():
            self.btn_order.setEnabled(False)
        else:
            self.btn_order.setEnabled(True)
    
    @footprint
    @pyqtSlot()
    def add1pct(self):
        if self.txt_btc.text() == "":
            self.txt_btc.setText("{0:.2f}".format(0.01))
        else:
            value = float(self.txt_btc.text())
            self.txt_btc.setText("{0:.2f}".format(value + 0.01))
    
    @footprint
    @pyqtSlot()
    def add10pct(self):
        if self.txt_btc.text() == "":
            self.txt_btc.setText("{0:.2f}".format(0.1))
        else:
            value = float(self.txt_btc.text())
            self.txt_btc.setText("{0:.2f}".format(value + 0.1))
    
    @footprint
    @pyqtSlot()
    def add100pct(self):
        if self.txt_btc.text() == "":
            self.txt_btc.setText("{0:.2f}".format(1))
        else:
            value = float(self.txt_btc.text())
            self.txt_btc.setText("{0:.2f}".format(value + 1))
    
    @footprint
    @pyqtSlot()
    def clearVolume(self):
        self.txt_btc.setText("0")
    
    @footprint
    @pyqtSlot()
    def updateExpectedValues(self):
        self.updateExpectedCurrent()
        self.updateExpectedGoal()
        self.updateExpectedStop()
    
    @footprint
    @pyqtSlot()
    def updateExpectedCurrent(self):
        if self.txt_btcjpy.text() == "":
            self.txt_btcjpy.setText("0")
        btc = float(self.txt_btc.text())
        btcjpy = float(self.txt_btcjpy.text())
        self.expected_current.setText(str(int(btc*btcjpy)))

    @footprint
    @pyqtSlot()
    def updateExpectedStop(self):
        btc = float(self.txt_btc.text())
        btcjpy = float(self.txt_btcjpy.text())
        if self.txt_stop.text() == "":
            self.txt_stop.setText("0")
            stop_value = 0
        else:
            stop_value = int(self.txt_stop.text())
        
        if self.btn_ask.isChecked():
            self.expected_stop.setText(str(int(btc * (btcjpy - stop_value))))
        else:
            self.expected_stop.setText(str(int(btc * (btcjpy + stop_value))))
    
    @footprint
    @pyqtSlot()
    def updateExpectedGoal(self):
        btc = float(self.txt_btc.text())
        btcjpy = float(self.txt_btcjpy.text())
        if self.txt_goal.text() == "":
            self.txt_goal.setText("0")
            goal_value = 0
        else:
            goal_value = int(self.txt_goal.text())

        if self.btn_ask.isChecked():
            self.expected_goal.setText(str(int(btc * (btcjpy + goal_value))))
        else:
            self.expected_goal.setText(str(int(btc * (btcjpy - goal_value))))
    
######################## GetDataProess functions ########################
    @footprint
    def initGetDataProcess(self):
        self._timer_getData = QTimer()
        self._timer_getData.setInterval(int(self._get_data_interval*1000))
        self.stopTimer = False
        self._thread_getData = QThread()
        self._worker_getData = GetTickerWorker(api=self._api, product_code=self._product_code)
        self._worker_getData.sleepInterval = self._get_data_worker_sleep_interval
        
        # Start.
        self._timer_getData.timeout.connect(self.startGettingDataThread)
        self._thread_getData.started.connect(self._worker_getData.process)
        self._worker_getData.do_something.connect(self.updateData)

        # Finish.
        self._worker_getData.finished.connect(self._thread_getData.quit)
        self._thread_getData.finished.connect(self.checkIsTimerStopped)

        # Move.
        self._worker_getData.moveToThread(self._thread_getData)
    
    @footprint
    @pyqtSlot()
    def startGettingDataThread(self):
        if not self._thread_getData.isRunning():
            print("start thread by timer.")
            self._thread_getData.start()
        else:
            print("Thread is running.")
    
    @footprint
    @pyqtSlot(object)
    def updateData(self, obj):
        mag = 100
        if obj is not None:
            try:
                if "timestamp" not in obj.keys():
                    print("Failure in getting ticker.")
                    return
                self.label_best_ask_value.setText(str(obj["best_ask"]))
                self.label_ltp_value.setText(str(obj["ltp"]))
                self.label_best_bid_value.setText(str(obj["best_bid"]))
                if self.chk_btcjpy.isChecked():
                    ltp = int(obj["ltp"])
                    ltp_to_set = (ltp // mag + 1) * mag
                    self.txt_btcjpy.setText(str(ltp_to_set))
            except Exception as ex:
                print(ex)
                return

    @footprint
    @pyqtSlot()
    def checkIsTimerStopped(self):
        if self.stopTimer:
            self._timer_getData.stop()
            print("timer stopped.")
            self.stopTimer = False
            self.btn_start_ticker.setEnabled(True)
            self.btn_start_ticker.setText("Start")


def main():
    app = QtGui.QApplication([])
    mw = OrderBoard()
    mw.show()
    app.exec_()

if __name__ == "__main__":
    main()
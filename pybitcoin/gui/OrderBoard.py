# -*- coding: utf-8 -*-

import datetime
import time
import os
import json
import pickle
import glob
import pybitflyer

from PyQt5.QtWidgets import QMainWindow, QGridLayout, QMenu, QWidget, QLabel, QLineEdit, QTextEdit
from PyQt5.QtWidgets import QCheckBox, qApp
from PyQt5.QtGui import QIcon, QPalette, QColor, QPixmap
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QPushButton, QMessageBox, QGroupBox, QDialog, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QStyle
from PyQt5.QtCore import pyqtSlot, QThread, QTimer, Qt, QMutex
from pyqtgraph.Qt import QtGui, QtCore

# import pyqtgraph as pg

from utils.decorator import footprint
from Worker import GetTickerWorker



class OrderBoard(QMainWindow):
    """OrderBoard class
    """
    
    def __init__(self, filepath=""):
        super().__init__()
        self.initInnerParameters(filepath)
        self.initGui()
        # For QPushButton on QMassageBox
        str_ = "background-color:{0};".format(self._init_button_color)
        qApp.setStyleSheet("QMessageBox::QPushButton{" + str_ + "}")
        qApp.setStyleSheet("QMessageBox::QPushButton{" + str_ + "}")
        self.initGetDataProcess()
    
    @footprint
    def initInnerParameters(self, filepath):
        """initInnerParameters(self, filepath) -> None
        Initialize the inner parameters.
        """

        """ Parameters for the GUI """
        self._mutex = QMutex()
        # self._windows = []
        self.initData()
        self._font_size_button = 13 # [pixel]
        self._font_size_groupbox_title = 12 # [pixel]
        self._font_size_label = 11 # [pixel]
        self._font_bold_label = True
        self._init_window_width = 260 # [pixel]
        self._init_window_height = 675 # [pixel]
        self._init_button_color = "#EBF5FB"
        self._txt_bgcolor = "#D0D3D4"
        self.main_bgcolor = "#566573"

        self._get_data_interval = 1 # [sec]
        self._get_data_worker_sleep_interval = self._get_data_interval - 0.1 # [sec]

        self._currentDir = os.path.dirname(__file__)
        self._closing_dialog = True
        
        """ Parameters for BTC trade """
        # for API
        self._product_code = "FX_BTC_JPY"
        self._api_dir = ".prv"
        # fldrname_for_key = getpass.getpass("folder for key:")
        if os.name == "nt":
            fpath = glob.glob(os.path.join(os.environ["USERPROFILE"], self._api_dir, "*"))[0]
        else:
            fpath = glob.glob(os.path.join(os.environ["HOME"], self._api_dir, "*"))[0]

        with open(fpath, "r", encoding="utf-8") as ff:
            try:
                self._api_key = ff.readline().strip()
                self._api_secret = ff.readline().strip()
            except Exception as ex:
                print(ex)
        
        self._api = pybitflyer.API(api_key=self._api_key, api_secret=self._api_secret)
        try:
            endpoint = "/v1/markets"
            _ = self._api.request(endpoint)
            print(_)
        except Exception as ex:
            print(ex)
        
        # for setting BTCJPY
        self._magnitude = 20

        # if os.path.exists(os.path.join(os.path.dirname(__file__), "config.json")):
        #     self.loadConfig()
        # if os.path.exists(filepath):
        #     self.loadConfigGetData(filepath)

        """ Parameters for emulation """
        self.__DEBUG = False
    
    @footprint
    @pyqtSlot()
    def initData(self):
        """ initData(self) -> None
        Initialize inner data.
        """
        self._executions = []
        self._contracts = []
        self._execution_count = 0

######################## Construction of GUI ########################
    @footprint
    def initMainWidget(self):
        """ initMainWidget(self) -> None
        Initialize the main widget and the grid.
        """
        self.main_widget = QWidget(self)
        self.setStyleSheet("background-color:{};".format(self.main_bgcolor))
        self.grid = QGridLayout(self.main_widget)
        self.grid.setSpacing(5)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "python.png")))
    
    @footprint
    def initGui(self):
        """initGui(self) -> None
        Initialize the GUI.
        """
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.initMainWidget()
        self.setMenuBar()

        if self.__DEBUG:
            self.setWindowTitle("Order Board(Emulate)")
        else:
            self.setWindowTitle("Order Board")
        self.resize(self._init_window_width, self._init_window_height)

        """ Board information """
        group_boardinfo, grid_boardinfo = \
            self.__makeGroupboxAndGrid(self, self._init_window_width - 20, 50, 
                                       "Board Info.", self._font_size_groupbox_title, 5)

        # Best ask
        label_best_ask = self.__makeLabel(group_boardinfo, "Ask: ", self._font_size_label, 
                                     isBold=self._font_bold_label, alignment=Qt.AlignRight)
        
        self.label_best_ask_value = \
            self.__makeLabel(group_boardinfo, "-1", self._font_size_label, 
                             isBold=self._font_bold_label, alignment=Qt.AlignLeft, color="#16A085")

        # Last execution
        label_ltp = self.__makeLabel(group_boardinfo, "LTP: ", self._font_size_label, 
                                     isBold=self._font_bold_label, alignment=Qt.AlignRight)
        
        self.label_ltp_value = \
            self.__makeLabel(group_boardinfo, "-1", self._font_size_label, 
                             isBold=self._font_bold_label, alignment=Qt.AlignLeft, color="#0B5345")

        # Best bid
        label_best_bid = self.__makeLabel(group_boardinfo, "Bid: ", self._font_size_label, 
                                     isBold=self._font_bold_label, alignment=Qt.AlignRight)
        
        self.label_best_bid_value = \
            self.__makeLabel(group_boardinfo, "-1 ", self._font_size_label, 
                             isBold=self._font_bold_label, alignment=Qt.AlignLeft, color="#EC7063")
        
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
                                       "Start from", self._font_size_groupbox_title, 5)
        
        self.btn_ask = self.__makePushButton(group_bidask, (self._init_window_width - 40)//2, 20, 
                                             "Ask", self._font_size_button, None, 
                                             color="#16A085")
        self.btn_ask.setCheckable(True)
        self.btn_ask.clicked.connect(self.updateOnAsk)
        
        self.btn_bid = self.__makePushButton(group_bidask, (self._init_window_width - 40)//2, 20, 
                                             "Bid", self._font_size_button, None, 
                                             color="#EC7063")
        self.btn_bid.setCheckable(True)
        self.btn_bid.clicked.connect(self.updateOnBid)

        # construct the layout
        grid_bidask.addWidget(self.btn_ask, 0, 0)
        grid_bidask.addWidget(self.btn_bid, 0, 1)

        """ Volume buttons """
        group_volume, grid_volume = \
            self.__makeGroupboxAndGrid(self, self._init_window_width - 20, 30, 
                                       "Volume (BTC)", self._font_size_groupbox_title, 5)

        # +0.01 BTCs button
        self.btn_1pct = self.__makePushButton(group_volume, 
                                               (self._init_window_width - 40)//4, 20, 
                                               "+0.01", self._font_size_button, self.add1pct, 
                                               color=self._init_button_color, isBold=True)

        # +0.1 BTCs button
        self.btn_10pct = self.__makePushButton(group_volume, 
                                               (self._init_window_width - 40)//4, 20, 
                                               "+0.1", self._font_size_button, self.add10pct, 
                                               color=self._init_button_color, isBold=True)

        # +1 BTCs button
        self.btn_100pct = self.__makePushButton(group_volume, 
                                               (self._init_window_width - 40)//4, 20, 
                                               "+1", self._font_size_button, self.add100pct, 
                                               color=self._init_button_color, isBold=True)

        # clear button
        self.btn_clear = self.__makePushButton(group_volume, 
                                               (self._init_window_width - 40)//4, 20, 
                                               "C", self._font_size_button, self.clearSize, 
                                               color=self._init_button_color, isBold=True)

        # construct the layout
        grid_volume.addWidget(self.btn_1pct, 0, 0)
        grid_volume.addWidget(self.btn_10pct, 0, 1)
        grid_volume.addWidget(self.btn_100pct, 0, 2)
        grid_volume.addWidget(self.btn_clear, 0, 3)

        """ Value setting """
        group_values, grid_values = \
            self.__makeGroupboxAndGrid(self, self._init_window_width - 20, 50, 
                                       "Values", self._font_size_groupbox_title, 5)
        
        # BTC volume
        label_btc_size = self.__makeLabel(group_values, "Size", self._font_size_label, 
                                            isBold=self._font_bold_label, alignment=Qt.AlignLeft)

        self.txt_btc = QLineEdit(group_values)
        self.txt_btc.setText("0")
        font = self.txt_btc.font()
        font.setPointSize(self._font_size_button)
        self.txt_btc.setFont(font)
        self.txt_btc.resize((self._init_window_width - 50)//2, 16)
        self.txt_btc.setStyleSheet("background-color:{};".format(self._txt_bgcolor))
        self.txt_btc.setValidator(QDoubleValidator())
        self.txt_btc.textChanged.connect(self.updateExpectedValues)

        label_btc_unit = self.__makeLabel(group_values, "B", self._font_size_label, 
                                            isBold=self._font_bold_label, alignment=Qt.AlignLeft)
        
        # BTCJPY
        ## Auto-manual flag checkbox
        self.chk_btcjpy = QCheckBox(group_values)
        self.chk_btcjpy.setChecked(True)
        self.chk_btcjpy.resize(20, 20)
        self.chk_btcjpy.stateChanged.connect(self.setTxtBTCJPYEditState)

        ## TextBox
        self.txt_btcjpy = QLineEdit(group_values)
        self.txt_btcjpy.setText("0")
        font = self.txt_btcjpy.font()
        font.setPointSize(self._font_size_button)
        self.txt_btcjpy.setFont(font)
        self.txt_btcjpy.resize((self._init_window_width - 50)//2, 16)
        self.txt_btcjpy.setStyleSheet("background-color:{};".format(self._txt_bgcolor))
        self.txt_btcjpy.setValidator(QIntValidator())
        self.txt_btcjpy.textChanged.connect(self.updateExpectedValues)
        self.txt_btcjpy.setReadOnly(True)

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
        self.txt_stop.resize((self._init_window_width - 50)//2, 16)
        self.txt_stop.setStyleSheet("background-color:{};".format(self._txt_bgcolor))
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
        self.txt_goal.resize((self._init_window_width - 50)//2, 16)
        self.txt_goal.setStyleSheet("background-color:{};".format(self._txt_bgcolor))
        self.txt_goal.setValidator(QIntValidator())
        self.txt_goal.textChanged.connect(self.updateExpectedGoal)

        label_goal_unit = self.__makeLabel(group_values, "yen", self._font_size_label, 
                                           isBold=self._font_bold_label, alignment=Qt.AlignLeft)

        # construct the layout
        grid_values.addWidget(label_btc_size, 0, 0)
        grid_values.addWidget(self.txt_btc, 0, 1)
        grid_values.addWidget(label_btc_unit, 0, 2)
        
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
                                       "Expected values", self._font_size_groupbox_title, 5)
        
        # Expected current value
        label_expected_current = self.__makeLabel(group_expected, "Current: ", self._font_size_label, 
                                                  isBold=self._font_bold_label, alignment=Qt.AlignRight)
        
        self.expected_current = self.__makeLabel(group_expected, "0", self._font_size_label, 
                                                 isBold=self._font_bold_label, alignment=Qt.AlignLeft)

        # Expected stop value
        label_expected_stop = self.__makeLabel(group_expected, "Stop: ", self._font_size_label, 
                                               isBold=self._font_bold_label, alignment=Qt.AlignRight)
        
        self.expected_stop = self.__makeLabel(group_expected, "0", self._font_size_label, 
                                              isBold=self._font_bold_label, alignment=Qt.AlignLeft)
        
        # Expected goal value
        label_expected_goal = self.__makeLabel(group_expected, "Goal: ", self._font_size_label, 
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


        """ Order/Execution """
        group_order, grid_order = \
            self.__makeGroupboxAndGrid(self, self._init_window_width - 20, 100, 
                                       "Order/Get Exec", self._font_size_groupbox_title, 5)

        # Order button
        self.btn_order = self.__makePushButton(group_order, (self._init_window_width - 50)//2, 20, 
                                               "Order", self._font_size_button, self.order, 
                                               color=self._init_button_color, isBold=True)
        self.btn_order.setEnabled(False)

        # Get last execution button
        self.btn_get_ex = self.__makePushButton(group_order, (self._init_window_width - 50)//2, 20, 
                                                 "Get Exec", self._font_size_button, self.getLastExecution, 
                                                 color=self._init_button_color, isBold=True)
        

        # Order/Execution Log
        self.txt_log = QTextEdit(group_order)
        self.txt_log.setText("Log is shown here.")
        font = self.txt_log.font()
        font.setPointSize(self._font_size_button)
        self.txt_log.setFont(font)
        self.txt_log.resize(self._init_window_width - 20, 50)
        self.txt_log.setStyleSheet("background-color:{};".format("white"))
        self.txt_log.setReadOnly(True)
        
        # construct the layout
        grid_order.addWidget(self.btn_order, 0, 0)
        grid_order.addWidget(self.btn_get_ex, 0, 1)
        grid_order.addWidget(self.txt_log, 1, 0, 1, 2)

        """ add all the widget """
        self.grid.addWidget(group_boardinfo, 0, 0)
        self.grid.addWidget(group_bidask, 1, 0)
        self.grid.addWidget(group_volume, 2, 0)
        self.grid.addWidget(group_values, 3, 0)
        self.grid.addWidget(group_expected, 4, 0)
        self.grid.addWidget(group_order, 5, 0)

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
    
    def __makePushButton(self, parent, width, height, text, fontsize, method=None, color=None, isBold=False):
        """__makePushButton(self, parent, width, height, text, fontsize, method, color, isBold) -> QPushButton

        Parameters
        ----------
        parent : class overtaking QtWidgets
        width : int
        height : int
        text : str
        fontsize : str
        method : function
        color : str (color code)
        isBold : bool

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
    
    @footprint
    def setMenuBar(self):
        """setMenuBar(self) -> None
        Set the contents of the menu bar
        """
        # File
        file_menu = QMenu('&File', self)

        ## Open
        # file_menu.addAction('&Open', self.openFile,
        #         QtCore.Qt.CTRL + QtCore.Qt.Key_O)

        ## Config
        file_menu.addAction('&Config', self.setConfig,
                QtCore.Qt.CTRL + QtCore.Qt.Key_C)
        
        ## Quit
        file_menu.addAction('&Quit', self.quitApp,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        
        self.menuBar().addMenu(file_menu)

        # Help
        # help_menu = QMenu('&Help', self)
        # help_menu.addAction('Help', self.showHelp)
        # help_menu.addAction('About...', self.showAbout)
        # self.menuBar().addSeparator()
        # self.menuBar().addMenu(help_menu)

######################## Menu bar ########################
    @footprint
    def setConfig(self):
        """setConfig(self) -> None
        Set configuration of this application.
        """
        pass

    @footprint
    def quitApp(self):
        """quitApp(self) -> None
        Quit this application.
        """
        self.close()
    
######################## Widgets' functions ########################
    @footprint
    @pyqtSlot()
    def runAutoGetTicker(self):
        """runAutoGetTicker(self) -> None
        run a function to get ticker on another thread
        """
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
        """getTickerMaually(self) -> None
        get ticker
        """
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
                ltp_to_set = (ltp // self._magnitude + 1) * self._magnitude
                self.txt_btcjpy.setText(str(ltp_to_set))
        except Exception as ex:
            print(ex)
            return

    @footprint
    @pyqtSlot()
    def updateOnAsk(self):
        """updateOnAsk(self) -> None
        update values when Ask button is pushed
        """
        self.btn_bid.setChecked(False)
        self.checkValidationOfOrder()
        self.updateExpectedStop()
        self.updateExpectedGoal()
    
    @footprint
    @pyqtSlot()
    def updateOnBid(self):
        """updateOnBid(self) -> None
        update values when Bid button is pushed
        """
        self.btn_ask.setChecked(False)
        self.checkValidationOfOrder()
        self.updateExpectedStop()
        self.updateExpectedGoal()
    
    @footprint
    @pyqtSlot()
    def checkValidationOfOrder(self):
        """checkValidationOfOrder(self) -> None
        check validation of the order
        """
        if not self.btn_ask.isChecked() and not self.btn_bid.isChecked():
            self.btn_order.setEnabled(False)
        else:
            self.btn_order.setEnabled(True)
    
    @footprint
    @pyqtSlot()
    def add1pct(self):
        """add1pct(self) -> None
        add 0.01 BTC to the order size
        """
        if self.txt_btc.text() == "":
            self.txt_btc.setText("{0:.2f}".format(0.01))
        else:
            value = float(self.txt_btc.text())
            self.txt_btc.setText("{0:.2f}".format(value + 0.01))
    
    @footprint
    @pyqtSlot()
    def add10pct(self):
        """add10pct(self) -> None
        add 0.1 BTC to the order size
        """
        if self.txt_btc.text() == "":
            self.txt_btc.setText("{0:.2f}".format(0.1))
        else:
            value = float(self.txt_btc.text())
            self.txt_btc.setText("{0:.2f}".format(value + 0.1))
    
    @footprint
    @pyqtSlot()
    def add100pct(self):
        """add100pct(self) -> None
        add 1 BTC to the order size
        """
        if self.txt_btc.text() == "":
            self.txt_btc.setText("{0:.2f}".format(1))
        else:
            value = float(self.txt_btc.text())
            self.txt_btc.setText("{0:.2f}".format(value + 1))
    
    @footprint
    @pyqtSlot()
    def clearSize(self):
        """clearSize(self) -> None
        clear the order size
        """
        self.txt_btc.setText("0")
    
    @footprint
    def setTxtBTCJPYEditState(self, state):
        """setTxtBTCJPYEditState(self, state) -> None
        """
        if state == 2:
            self.txt_btcjpy.setReadOnly(True)
        else:
            self.txt_btcjpy.setReadOnly(False)
    
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
    
    @footprint
    @pyqtSlot()
    def order(self):
        """order(self) -> response
        """
        # get size and prices
        btcjpy = int(self.txt_btcjpy.text())
        btc = float(self.txt_btc.text())
        if self.btn_ask.isChecked():
            stop = btcjpy - int(self.txt_stop.text())
            goal = btcjpy + int(self.txt_goal.text())
            side_ifd = "BUY"
            side_oco = "SELL"
        else:
            stop = btcjpy + int(self.txt_stop.text())
            goal = btcjpy - int(self.txt_goal.text())
            side_ifd = "SELL"
            side_oco = "BUY"
        
        # IFDOCO setting
        ## IDF
        params_ifd = {
            "product_code":self._product_code,
            "condition_type":"LIMIT",
            "side":side_ifd,
            "price":btcjpy,
            "size":btc
        }

        ## OCO1: stop
        params_oco1 = {
            "product_code":self._product_code,
            "condition_type":"STOP",
            "side":side_oco,
            "trigger_price":stop,
            "size":btc
        }

        ## OCO2: goal
        params_oco2 = {
            "product_code":self._product_code,
            "condition_type":"STOP",
            "side":side_oco,
            "trigger_price":goal,
            "size":btc
        }

        params = {
            "order_method":"IFDOCO",
            "minute_to_expire":10,
            "parameters":[params_ifd, params_oco1, params_oco2],

        }
        try:
            if self.__DEBUG:
                print(params)
                self._execution_count += 1
                result = {"parent_order_acceptance_id":str(self._execution_count)}
            else:
                result = self._api.sendparentorder(**params)
            
            print(result)
        except Exception as ex:
            print("@ sending order:", ex)
        
        try:
            if "parent_order_acceptance_id" not in result:
                parent_order_acceptance_id = self._execution_count
                message = "no data of 'parent_order_acceptance_id'"
            else:
                parent_order_acceptance_id = result["parent_order_acceptance_id"]
                message = result["parent_order_acceptance_id"]
            
            self._executions.append(
                dict(
                    param=params, 
                    parent_order_acceptance_id=parent_order_acceptance_id
                )
            )
            self.saveLastExecution()
        except Exception as ex:
            print("@ saving an order:", ex)
        
        try:
            self.txt_log.append("order id: " + message)
            # self.txt_log.scrollToAnchor()
        except Exception as ex:
            print("@ logging:", ex)
            

        except Exception as ex:
            print(ex)
    
    @footprint
    def saveExecutions(self):
        if len(self._executions) <= 0:
            return
        datetimeFmt = "%Y%m%d%H%M%S"
        now = datetime.datetime.now().strftime(datetimeFmt)
        fpath = os.path.join(os.path.dirname(__file__), "data", "{}.json".format(now))
        history = dict(executions=self._executions)
        with open(fpath, "w") as ff:
            json.dump(history, ff, indent=4)
    
    @footprint
    def saveLastExecution(self):
        if len(self._executions) <= 0:
            return
        tmpfldr = os.path.join(os.path.dirname(__file__), "tmp")
        if not os.path.exists(tmpfldr):
            os.mkdir(tmpfldr)
        datetimeFmt = "%Y%m%d%H%M%S"
        now = datetime.datetime.now().strftime(datetimeFmt)
        fpath = os.path.join(os.path.dirname(__file__), "tmp", "{}.json".format(now))
        history = dict(executions=self._executions)
        with open(fpath, "w") as ff:
            json.dump(history, ff, indent=4)

    @footprint
    @pyqtSlot()
    def getLastExecution(self):
        # last_execution = self._executions[-1]
        # parent_order_id = last_execution["parent_order_id"]
        count = 2
        results = self._api.getexecutions(product_code=self._product_code, count=count)
        for ii in range(len(results)):
            result = results[-ii-1]
            result_str = "{0} {1} {2} {3}".\
                format(result["exec_date"], result["side"], result["price"], result["size"])
            self.txt_log.append(result_str)
            # self.txt_log.scrollToAnchor()
            # print(result["exec_date"])
            # print(result["side"], result["price"], result["size"])
            # print("")
    
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
        mag = 20
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

######################## Closing processes ########################
    @footprint
    def closeEvent(self, event):
        if self._thread_getData.isRunning():
            string = "Some threads are still running.\n"
            string += "Please wait for their finishing."
            confirmObject = QMessageBox.warning(self, "Closing is ignored.",
                string, QMessageBox.Ok)
            event.ignore()
            return
        if self._timer_getData.isActive():
            string = "Some timers are still running.\n"
            string += "Please wait for their finishing."
            confirmObject = QMessageBox.warning(self, "Closing is ignored.",
                string, QMessageBox.Ok)
            event.ignore()
            return
        if self._closing_dialog:
            confirmObject = QMessageBox.question(self, "Closing...",
                "Are you sure to quit?", QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
            if confirmObject == QMessageBox.Yes:
                self.stopAllTimers()
                self.saveExecutions()
                event.accept()
            else:
                event.ignore()
        else:
            self.stopAllTimers()
            self.saveExecutions()

    @footprint
    def stopAllTimers(self):
        if self._timer_getData.isActive():
            self._timer_getData.stop()

def main():
    app = QtGui.QApplication([])
    mw = OrderBoard()
    mw.show()
    app.exec_()

if __name__ == "__main__":
    main()
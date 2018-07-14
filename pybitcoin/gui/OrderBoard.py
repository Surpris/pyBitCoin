# -*- coding: utf-8 -*-

import datetime
import time
import os
import json
import pickle
import glob
import pybitflyer

from PyQt5.QtWidgets import QMainWindow, QGridLayout, QMenu, QWidget, QLabel, QLineEdit, QTextEdit
from PyQt5.QtWidgets import QCheckBox, QApplication, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QIcon, QPalette, QColor, QPixmap
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QPushButton, QMessageBox, QGroupBox, QDialog, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QStyle, QGraphicsView
from PyQt5.QtCore import pyqtSlot, QThread, QTimer, Qt, QMutex
from PyQt5 import  QtGui, QtCore

from utils import footprint
from utils import make_groupbox_and_grid, make_label, make_pushbutton
from Worker import GetTickerWorker

class OrderBoard(QMainWindow):
    """OrderBoard class (subclass of QMainWindow)
    """
    
    def __init__(self):
        """__init__(self)
        initialize the whole of this class.
        """
        super().__init__()
        self.initInnerParameters()
        self.initAPI()
        self.initData()
        self.initGui()
        # For QPushButton on QMassageBox
        str_ = "background-color:{0};".format(self._button_bg_color)
        self.initGetDataProcess()
    
    @footprint
    def initInnerParameters(self):
        """initInnerParameters(self) -> None
        initialize the inner parameters.
        """

        """ Parameters for the GUI """
        self._mutex = QMutex()
        # self._windows = []

        self._window_width = 360 # [pixel]
        self._window_height = 675 # [pixel]
        self._window_color = "#566573"

        self._groupbox_title_font_size = 12 # [pixel]

        self._label_font_size = 11 # [pixel]
        self._label_font_bold = True
        self._label_font_color = "white"

        self._button_font_size = 13 # [pixel]
        # self._button_font_color = "black"
        self._button_bg_color = "#EBF5FB"
        
        # self._txt_font_color = "black"
        self._txt_bg_color = "#D0D3D4"
        
        self._ask_color = "#16A085"
        self._bid_color = "#EC7063"

        self._get_data_interval = 1 # [sec]
        self._get_data_worker_sleep_interval = self._get_data_interval - 0.1 # [sec]

        self._currentDir = os.path.dirname(__file__)
        self._closing_dialog = True

        self._datetimeFmt_DATA = "%Y%m%d%H%M%S"
        self._datetimeFmt_LOG = "%Y-%m-%d %H:%M:%S"
        
        """ Parameters for BTC trade """
        # for API
        self._product_code = "FX_BTC_JPY"
        self._api_dir = ".prv"

        # for setting BTCJPY
        self._magnitude = 20
        self._default_value = "0"
        self._datetimeFmt_BITFLYER = "%Y-%m-%dT%H:%M:%S.%f"

        # order type
        # self._order_type = "ifdoco"
        self._order_type = "child"
        self._order_condition = "MARKET"

        """ Some other parameters """
        self.__DEBUG = False
        # self.__log_level = "None"

        # """ Load configuration from the setting file """
        # if os.path.exists(os.path.join(os.path.dirname(__file__), "config.json")):
        #     self.loadConfig()

    @footprint
    def initAPI(self):
        """self.initData() -> None
        initialize the API of pybitflyer.
        """
        if os.name == "nt":
            fpath = glob.glob(os.path.join(os.environ["USERPROFILE"], self._api_dir, "*"))[0]
        else:
            fpath = glob.glob(os.path.join(os.environ["HOME"], self._api_dir, "*"))[0]

        # raise the exception unless both an API key and an API secret key are not loaded.
        with open(fpath, "r", encoding="utf-8") as ff:
            try:
                self._api_key = ff.readline().strip()
                self._api_secret = ff.readline().strip()
            except Exception as ex:
                raise Exception(ex)
        
        self._api = pybitflyer.API(api_key=self._api_key, api_secret=self._api_secret)
        self.__API_ERROR = False
        try:
            endpoint = "/v1/markets"
            currencies = self._api.request(endpoint)
            if isinstance(currencies, list):
                print("Currency:")
                print([currency["product_code"] for currency in currencies])
            else:
                print("No available currencies.")
                self.__API_ERROR = True
            
            endpoint = "/v1/me/getpermissions"
            permissions = self._api.request(endpoint)
            if isinstance(permissions, list):
                print("Permitted API:")
                print(permissions)
            else:
                print("No permitted APIs.")
                self.__API_ERROR = True
        except Exception as ex:
            print(ex)
            self.__API_ERROR = True
    
    @footprint
    def initData(self):
        """ initData(self) -> None
        initialize inner data.
        """
        self._executions = []
        self._contracts = []
        self._execution_count = 0
        self._last_exec = dict()
        self._last_order = dict()
        self._order_interest = dict()

######################## Construction of GUI ########################
    @footprint
    def initMainWidget(self):
        """ initMainWidget(self) -> None
        initialize the main widget and its grid.
        """
        self.main_widget = QWidget(self)
        self.setStyleSheet("background-color:{};".format(self._window_color))
        self.grid = QGridLayout(self.main_widget)
        self.grid.setSpacing(5)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "python.png")))
    
    @footprint
    def initGui(self):
        """initGui(self) -> None
        initialize the GUI.
        """
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.initMainWidget()
        self.setMenuBar()

        if self.__DEBUG:
            self.setWindowTitle("Order Board(Emulate)")
        else:
            self.setWindowTitle("Order Board")
        self.resize(self._window_width, self._window_height)

        """ Bank information """
        group_bankinfo, grid_bankinfo = \
            make_groupbox_and_grid(self, (self._window_width - 20)//3, 50, 
                                   "Board Info.", self._groupbox_title_font_size, 5)
        
        self.jpy_value = make_label(group_bankinfo, self._default_value, self._label_font_size, 
                                    isBold=self._label_font_bold, alignment=Qt.AlignRight, 
                                    color=self._label_font_color)
        
        self.btc_value = make_label(group_bankinfo, self._default_value, self._label_font_size, 
                                    isBold=self._label_font_bold, alignment=Qt.AlignRight, 
                                    color=self._label_font_color)

        self.tot_value = make_label(group_bankinfo, self._default_value, self._label_font_size, 
                                    isBold=self._label_font_bold, alignment=Qt.AlignRight, 
                                    color=self._label_font_color)
        
        grid_bankinfo.addWidget(self.jpy_value, 0, 0)
        grid_bankinfo.addWidget(self.btc_value, 1, 0)
        grid_bankinfo.addWidget(self.tot_value, 2, 0)

        """ Board information """
        group_boardinfo, grid_boardinfo = \
            make_groupbox_and_grid(self, (self._window_width - 20)*2//3, 50, 
                                   "Board Info.", self._groupbox_title_font_size, 5)

        # Best ask
        label_best_ask = make_label(group_boardinfo, "Ask: ", self._label_font_size, 
                                    isBold=self._label_font_bold, alignment=Qt.AlignRight)
        
        self.label_best_ask_value = \
            make_label(group_boardinfo, self._default_value, self._label_font_size, 
                       isBold=self._label_font_bold, alignment=Qt.AlignLeft, 
                       color=self._ask_color)

        # Last execution
        label_ltp = make_label(group_boardinfo, "LTP: ", self._label_font_size, 
                               isBold=self._label_font_bold, alignment=Qt.AlignRight)
        
        self.label_ltp_value = \
            make_label(group_boardinfo, self._default_value, self._label_font_size, 
                       isBold=self._label_font_bold, alignment=Qt.AlignLeft, 
                       color="lightgray")

        # Best bid
        label_best_bid = make_label(group_boardinfo, "Bid: ", self._label_font_size, 
                                    isBold=self._label_font_bold, alignment=Qt.AlignRight)
        
        self.label_best_bid_value = \
            make_label(group_boardinfo, self._default_value, self._label_font_size, 
                       isBold=self._label_font_bold, alignment=Qt.AlignLeft, 
                       color=self._bid_color)
        
        # Health/State
        self.health_info = \
            make_label(group_boardinfo, "STOP", self._label_font_size, 
                       isBold=self._label_font_bold, alignment=Qt.AlignLeft, 
                       color=self._label_font_color)
        
        self.state_info = \
            make_label(group_boardinfo, "CLOSED", self._label_font_size, 
                       isBold=self._label_font_bold, alignment=Qt.AlignLeft, 
                       color=self._label_font_color)
        
        self.btn_start_ticker = \
            make_pushbutton(group_boardinfo, 
                            (self._window_width - 40)//4, 60, 
                            "Start", self._button_font_size, self.runAutoGetTicker, 
                            color=self._button_bg_color)

        # construct the layout
        grid_boardinfo.addWidget(label_best_ask, 0, 0, 1, 1)
        grid_boardinfo.addWidget(self.label_best_ask_value, 0, 1, 1, 1)

        grid_boardinfo.addWidget(label_ltp, 1, 0, 1, 1)
        grid_boardinfo.addWidget(self.label_ltp_value, 1, 1, 1, 1)

        grid_boardinfo.addWidget(label_best_bid, 2, 0, 1, 1)
        grid_boardinfo.addWidget(self.label_best_bid_value, 2, 1, 1, 1)

        grid_boardinfo.addWidget(self.health_info, 0, 2, 1, 1)
        grid_boardinfo.addWidget(self.state_info, 1, 2, 1, 1)
        grid_boardinfo.addWidget(self.btn_start_ticker, 2, 2, 1, 1)

        """ Bid / Ask / Order """
        group_bidask, grid_bidask = \
            make_groupbox_and_grid(self, self._window_width - 20, 30, 
                                   "Order", self._groupbox_title_font_size, 5)
        
        label_expected_current = make_label(group_bidask, "Current: ", self._label_font_size, 
                                            isBold=self._label_font_bold, alignment=Qt.AlignRight)

        self.expected_current = make_label(group_bidask, self._default_value, self._label_font_size, 
                                           isBold=self._label_font_bold, alignment=Qt.AlignLeft, 
                                           color=self._label_font_color)

        self.btn_ask = make_pushbutton(group_bidask, (self._window_width - 40)//6, 20, 
                                       "Ask", self._button_font_size, None, 
                                       color=self._ask_color)
        self.btn_ask.setCheckable(True)
        self.btn_ask.clicked.connect(self.updateOnAsk)
        
        self.btn_bid = make_pushbutton(group_bidask, (self._window_width - 40)//6, 20, 
                                       "Bid", self._button_font_size, None, 
                                       color=self._bid_color)
        self.btn_bid.setCheckable(True)
        self.btn_bid.clicked.connect(self.updateOnBid)

        self.btn_order = make_pushbutton(group_bidask, (self._window_width - 50)//3, 20, 
                                         "Order", self._button_font_size, self.order, 
                                         color=self._button_bg_color, isBold=True)
        self.btn_order.setEnabled(False)

        # construct the layout
        grid_bidask.addWidget(label_expected_current, 0, 0)
        grid_bidask.addWidget(self.expected_current, 0, 1)
        grid_bidask.addWidget(self.btn_ask, 1, 0)
        grid_bidask.addWidget(self.btn_bid, 1, 1)
        grid_bidask.addWidget(self.btn_order, 2, 0, 1, 2)

        """ Volume buttons """
        group_volume, grid_volume = \
            make_groupbox_and_grid(self, self._window_width - 20, 30, 
                                   "Volume (BTC)", self._groupbox_title_font_size, 5)

        # +0.01 BTCs button
        self.btn_1pct = make_pushbutton(group_volume, 
                                        (self._window_width - 40)//4, 20, 
                                        "+0.01", self._button_font_size, self.add1pct, 
                                        color=self._button_bg_color, isBold=True)

        # +0.1 BTCs button
        self.btn_10pct = make_pushbutton(group_volume, 
                                         (self._window_width - 40)//4, 20, 
                                         "+0.1", self._button_font_size, self.add10pct, 
                                         color=self._button_bg_color, isBold=True)

        # +1 BTCs button
        self.btn_100pct = make_pushbutton(group_volume, 
                                          (self._window_width - 40)//4, 20, 
                                          "+1", self._button_font_size, self.add100pct, 
                                          color=self._button_bg_color, isBold=True)

        # clear button
        self.btn_clear = make_pushbutton(group_volume, 
                                         (self._window_width - 40)//4, 20, 
                                         "C", self._button_font_size, self.clearSize, 
                                         color=self._button_bg_color, isBold=True)

        # construct the layout
        grid_volume.addWidget(self.btn_1pct, 0, 0)
        grid_volume.addWidget(self.btn_10pct, 0, 1)
        grid_volume.addWidget(self.btn_100pct, 0, 2)
        grid_volume.addWidget(self.btn_clear, 0, 3)

        """ Value setting """
        group_values, grid_values = \
            make_groupbox_and_grid(self, self._window_width - 20, 50, 
                                   "Values", self._groupbox_title_font_size, 5)
        
        # BTC volume
        label_btc_size = make_label(group_values, "Size", self._label_font_size, 
                                    isBold=self._label_font_bold, alignment=Qt.AlignLeft)

        self.txt_btc = QLineEdit(group_values)
        self.txt_btc.setText("0")
        font = self.txt_btc.font()
        font.setPointSize(self._button_font_size)
        self.txt_btc.setFont(font)
        self.txt_btc.resize((self._window_width - 50)//3, 16)
        self.txt_btc.setStyleSheet("background-color:{};".format(self._txt_bg_color))
        self.txt_btc.setValidator(QDoubleValidator())
        self.txt_btc.textChanged.connect(self.updateExpectedValues)

        label_btc_unit = make_label(group_values, "B", self._label_font_size, 
                                    isBold=self._label_font_bold, alignment=Qt.AlignLeft)
        
        # BTCJPY
        ## Auto-manual flag checkbox
        self.chk_btcjpy = QCheckBox(group_values)
        self.chk_btcjpy.setChecked(True)
        self.chk_btcjpy.resize(20, 20)
        self.chk_btcjpy.stateChanged.connect(self.setTxtBTCJPYEditState)

        ## TextBox
        self.txt_btcjpy = QLineEdit(group_values)
        self.txt_btcjpy.setText(self._default_value)
        font = self.txt_btcjpy.font()
        font.setPointSize(self._button_font_size)
        self.txt_btcjpy.setFont(font)
        self.txt_btcjpy.resize((self._window_width - 50)//3, 16)
        self.txt_btcjpy.setStyleSheet("background-color:{};".format(self._txt_bg_color))
        self.txt_btcjpy.setValidator(QIntValidator())
        self.txt_btcjpy.textChanged.connect(self.updateExpectedValues)
        self.txt_btcjpy.setReadOnly(True)

        label_jpy_unit = make_label(group_values, "yen", self._label_font_size, 
                                    isBold=self._label_font_bold, alignment=Qt.AlignLeft)
        
        # Stop value (relative)
        label_stop = make_label(group_values, "Stop: ", self._label_font_size, 
                                isBold=self._label_font_bold, alignment=Qt.AlignLeft)
        
        self.txt_stop = QLineEdit(group_values)
        self.txt_stop.setText(self._default_value)
        font = self.txt_stop.font()
        font.setPointSize(self._button_font_size)
        self.txt_stop.setFont(font)
        self.txt_stop.resize((self._window_width - 50)//3, 16)
        self.txt_stop.setStyleSheet("background-color:{};".format(self._txt_bg_color))
        self.txt_stop.setValidator(QIntValidator())
        # self.txt_stop.textChanged.connect(self.updateExpectedStop)
        self.txt_stop.setReadOnly(True)

        label_stop_unit = make_label(group_values, "yen", self._label_font_size, 
                                     isBold=self._label_font_bold, alignment=Qt.AlignLeft)

        # Goal value (relative)
        label_goal = make_label(group_values, "Goal: ", self._label_font_size, 
                                isBold=self._label_font_bold, alignment=Qt.AlignLeft)
        
        self.txt_goal = QLineEdit(group_values)
        self.txt_goal.setText(self._default_value)
        font = self.txt_goal.font()
        font.setPointSize(self._button_font_size)
        self.txt_goal.setFont(font)
        self.txt_goal.resize((self._window_width - 50)//3, 16)
        self.txt_goal.setStyleSheet("background-color:{};".format(self._txt_bg_color))
        self.txt_goal.setValidator(QIntValidator())
        # self.txt_goal.textChanged.connect(self.updateExpectedGoal)
        self.txt_goal.setReadOnly(True)

        label_goal_unit = make_label(group_values, "yen", self._label_font_size, 
                                     isBold=self._label_font_bold, alignment=Qt.AlignLeft)

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
        # group_expected, grid_expected = \
        #     make_groupbox_and_grid(self, self._window_width - 20, 50, 
        #                                "Expected values", self._groupbox_title_font_size, 5)
        
        # Expected current value
        # label_expected_current = make_label(group_expected, "Expected: ", self._label_font_size, 
        #                                           isBold=self._label_font_bold, alignment=Qt.AlignRight)
        
        # self.expected_current = make_label(group_expected, self._default_value, self._label_font_size, 
        #                                          isBold=self._label_font_bold, alignment=Qt.AlignLeft)

        # Expected stop value
        # label_expected_stop = make_label(group_expected, "Stop: ", self._label_font_size, 
        #                                        isBold=self._label_font_bold, alignment=Qt.AlignRight)
        
        # self.expected_stop = make_label(group_expected, self._default_value, self._label_font_size, 
        #                                       isBold=self._label_font_bold, alignment=Qt.AlignLeft)
        
        # Expected goal value
        # label_expected_goal = make_label(group_expected, "Goal: ", self._label_font_size, 
        #                                        isBold=self._label_font_bold, alignment=Qt.AlignRight)
        
        # self.expected_goal = make_label(group_expected, self._default_value, self._label_font_size, 
        #                                       isBold=self._label_font_bold, alignment=Qt.AlignLeft)
        
        # construct the layout
        # grid_expected.addWidget(label_expected_current, 0, 0)
        # grid_expected.addWidget(self.expected_current, 0, 0)
        # grid_expected.addWidget(label_expected_stop, 1, 0)
        # grid_expected.addWidget(self.expected_stop, 1, 0)
        # grid_expected.addWidget(label_expected_goal, 2, 0)
        # grid_expected.addWidget(self.expected_goal, 2, 0)

        """ Current State Control """
        group_current, grid_current = \
            make_groupbox_and_grid(self, self._window_width - 20, 100, 
                                   "Current State Control", self._groupbox_title_font_size, 5)
        
        # Order button
        # self.btn_order = make_pushbutton(group_current, (self._window_width - 50)//2, 20, 
        #                                        "Order", self._button_font_size, self.order, 
        #                                        color=self._button_bg_color, isBold=True)
        # self.btn_order.setEnabled(False)

        # Get last execution button
        self.btn_get_ex = make_pushbutton(group_current, (self._window_width - 50)//4, 20, 
                                          "Exec", self._button_font_size, self.getLastExecution, 
                                          color=self._button_bg_color, isBold=True)
        
        # Get last order state button
        self.btn_get_los = make_pushbutton(group_current, (self._window_width - 50)//4, 20, 
                                           "Last Order", self._button_font_size, self.getLastOrderState, 
                                           color=self._button_bg_color, isBold=True)
        
        # Get order interest button
        self.btn_get_interest = \
            make_pushbutton(group_current, (self._window_width - 50)//4, 20, 
                            "Interest", self._button_font_size, self.getOrderInterest, 
                            color=self._button_bg_color, isBold=True)
        
        # cancel all order button
        self.btn_cancel_all = \
            make_pushbutton(group_current, (self._window_width - 50)//4, 20, 
                            "Cancel", self._button_font_size, self.cancelAllOrders, 
                            color=self._button_bg_color, isBold=True)
        
        # construct the layout
        # grid_current.addWidget(self.btn_order, 0, 0)
        grid_current.addWidget(self.btn_get_ex, 0, 0)
        grid_current.addWidget(self.btn_get_los, 0, 1)
        grid_current.addWidget(self.btn_get_interest, 0, 2)
        grid_current.addWidget(self.btn_cancel_all, 0, 3)

        """ Current state """
        self.current_table_header = ["Key", "Interest", "Exec", "LastOrder"]
        self.current_table_key = ["date", "side", "size", "price", "state"]
        self.current_table = QTableWidget(self)
        self.current_table.setColumnCount(len(self.current_table_header))
        self.current_table.setRowCount(len(self.current_table_key))
        font = self.current_table.font()
        # font.setPointSize(self._label_font_size)
        font.setBold(True)
        self.current_table.setFont(font)
        self.current_table.setStyleSheet("background-color:{};".format("white"))
        self.current_table.setHorizontalHeaderLabels(self.current_table_header)
        self.current_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.current_table.setFixedSize(self._window_width - 20, 180)

        """ Log """
        # Order/Execution Log
        self.txt_log = QTextEdit(group_current)
        self.txt_log.setText("Log is shown here.")
        font = self.txt_log.font()
        font.setPointSize(self._button_font_size)
        self.txt_log.setFont(font)
        self.txt_log.resize(self._window_width - 20, 30)
        self.txt_log.setStyleSheet("background-color:{};".format("white"))
        self.txt_log.setReadOnly(True)

        """ add all the widget """
        self.grid.addWidget(group_bankinfo, 0, 0, 1, 1)
        self.grid.addWidget(group_boardinfo, 0, 1, 1, 3)
        self.grid.addWidget(group_volume, 1, 0, 1, 4)
        # self.grid.addWidget(group_expected, 2, 0, 1, 1)
        self.grid.addWidget(group_values, 2, 0, 1, 3)
        self.grid.addWidget(group_bidask, 2, 3, 1, 1)
        self.grid.addWidget(group_current, 4, 0, 1, 4)
        self.grid.addWidget(self.current_table, 5, 0, 2, 4)
        self.grid.addWidget(self.txt_log, 7, 0, 1, 4)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        self.setFixedSize(self.size())
    
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
        self.checkValidationOfOrder()

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
        # self.updateExpectedStop()
        # self.updateExpectedGoal()
    
    @footprint
    @pyqtSlot()
    def updateOnBid(self):
        """updateOnBid(self) -> None
        update values when Bid button is pushed
        """
        self.btn_ask.setChecked(False)
        self.checkValidationOfOrder()
        # self.updateExpectedStop()
        # self.updateExpectedGoal()
    
    @footprint
    @pyqtSlot()
    def checkValidationOfOrder(self):
        """checkValidationOfOrder(self) -> None
        check validation of the order
        """
        if not self.btn_ask.isChecked() and not self.btn_bid.isChecked():
            self.btn_order.setEnabled(False)
        elif not self._timer_getData.isActive():
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
        """updateExpectedValues(self) -> None
        """
        self.updateExpectedCurrent()
        # self.updateExpectedGoal()
        # self.updateExpectedStop()
    
    @footprint
    @pyqtSlot()
    def updateExpectedCurrent(self):
        """updateExpectedCurrent(self) -> None
        """
        if self.txt_btcjpy.text() == "":
            self.txt_btcjpy.setText(self._default_value)
        btc = float(self.txt_btc.text())
        btcjpy = float(self.txt_btcjpy.text())
        self.expected_current.setText(str(int(btc*btcjpy)))

    @footprint
    @pyqtSlot()
    def updateExpectedStop(self):
        """updateExpectedStop(self) -> None
        """
        btc = float(self.txt_btc.text())
        btcjpy = float(self.txt_btcjpy.text())
        if self.txt_stop.text() == "":
            self.txt_stop.setText(self._default_value)
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
        """updateExpectedGoal(self) -> None
        """
        btc = float(self.txt_btc.text())
        btcjpy = float(self.txt_btcjpy.text())
        if self.txt_goal.text() == "":
            self.txt_goal.setText(self._default_value)
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
        """order(self) -> None
        wrapper function to send an order based on the setting of order.
        """
        if self._order_type == "ifdoco":
            self._sendIfdocoOrder()
        else:
            self._sendChildOrder()
    
    @footprint
    def _sendIfdocoOrder(self):
        """_sendIfdocoOrder(self) -> None
        send an IFDOCO order.
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
            "condition_type":"MARKET",
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
            self.txt_log.append("@ saving an order:", ex)
        
        try:
            self.txt_log.append("order id: " + message)
        except Exception as ex:
            self.txt_log.append("@ logging:", ex)
    
    @footprint
    def _sendChildOrder(self):
        """_sendChildOrder(self) -> None
        send an order.
        """
        # get size and prices
        btcjpy = int(self.txt_btcjpy.text())
        btc = float(self.txt_btc.text())
        if self.btn_ask.isChecked():
            side = "BUY"
        else:
            side = "SELL"
        
        # Order setting
        ## Child
        params = {
            "product_code":self._product_code,
            "child_order_type":self._order_condition,
            "side":side,
            "size":btc,
            "minute_to_expire":10
        }
        if self._order_condition == "LIMIT":
            params["price"] = btcjpy

        try:
            if self.__DEBUG:
                print(params)
                self._execution_count += 1
                result = {"child_order_acceptance_id":str(self._execution_count)}
            else:
                result = self._api.sendchildorder(**params)
            
            print(result)
        except Exception as ex:
            self.txt_log.append("@ sending order:", ex)
        
        try:
            if "child_order_acceptance_id" not in result:
                child_order_acceptance_id = self._execution_count
                message = "no data of 'child_order_acceptance_id'"
            else:
                child_order_acceptance_id = result["child_order_acceptance_id"]
                message = result["child_order_acceptance_id"]
            
            self._executions.append(
                dict(
                    date=datetime.datetime.now().strftime(self._datetimeFmt_DATA),
                    param=params, 
                    child_order_acceptance_id=child_order_acceptance_id
                )
            )
            self.saveLastExecution()
            self.screenShot()
        except Exception as ex:
            self.txt_log.append("@ saving an order:", ex)
        
        try:
            self.txt_log.append("order id: " + message)
        except Exception as ex:
            self.txt_log.append("@ logging:", ex)
    
    @footprint
    def saveExecutions(self):
        if len(self._executions) <= 0:
            return
        now = datetime.datetime.now().strftime(self._datetimeFmt_DATA)
        fpath = os.path.join(os.path.dirname(__file__), "data", "{}.json".format(now))
        history = dict(executions=self._executions)
        with open(fpath, "w") as ff:
            json.dump(history, ff, indent=4)
    
    @footprint
    def saveLastExecution(self):
        """saveLastExecution(self) -> None
        """
        if len(self._executions) <= 0:
            return
        tmpfldr = os.path.join(os.path.dirname(__file__), "tmp")
        if not os.path.exists(tmpfldr):
            os.mkdir(tmpfldr)
        now = datetime.datetime.now().strftime(self._datetimeFmt_DATA)
        fpath = os.path.join(os.path.dirname(__file__), "tmp", "{}.json".format(now))
        history = dict(executions=self._executions)
        with open(fpath, "w") as ff:
            json.dump(history, ff, indent=4)
    
    @footprint
    def screenShot(self):
        imgfldr = "./images"
        if not os.path.exists(imgfldr):
            os.mkdir(imgfldr)
        now = datetime.datetime.now().strftime(self._datetimeFmt_DATA)
        preview_window = QApplication.primaryScreen().grabWindow(0)
        preview_window.save(os.path.join(imgfldr, "{}_screenshot.png".format(now)), "png")
        # view = QGraphicsView()
        # view.show()
        # view.grab().save(os.path.join(imgfldr, "{}_screenshot.png".format(now)))

    @footprint
    @pyqtSlot()
    def getLastExecution(self):
        """getLastExecution(self) -> None
        """

        self.__getLastExecution()
        self.updateCurrentTable()
    
    def __getLastExecution(self):
        count = 1
        try:
            results = self._api.getexecutions(product_code=self._product_code, count=count)
            if len(results) <= 0:
                self._last_exec = dict()
                self.txt_log.append("{}: No executions.".\
                                    format(datetime.datetime.now().strftime(self._datetimeFmt_LOG)))
                return
            
            result = results[0]
            if not isinstance(result, dict):
                self._last_exec = dict()
                self.txt_log.append("{}: result has an unacceptable type = '{}'.".\
                                    format(datetime.datetime.now().strftime(self._datetimeFmt_LOG), 
                                        type(result)))
                return
            if "exec_date" not in result.keys():
                self._last_exec = dict()
                self.txt_log.append("{}: No executions.".\
                                    format(datetime.datetime.now().strftime(self._datetimeFmt_LOG)))
                return
        except Exception as ex:
            self.txt_log.append("@ getting executions:", ex)
            return
        
        try:
            for key in self.current_table_key:
                if key == "date":
                    self._last_exec[key] = result["exec_date"].split("T")[-1][:8]
                elif key == "state":
                    self._last_exec[key] = result["commission"]
                else:
                    self._last_exec[key] = result[key]
        except KeyError as ex:
            self.txt_log.append("@ updating the last execution:", ex)
            return
    
    @footprint
    @pyqtSlot()
    def getLastOrderState(self):
        """getLastOrderState(self) -> None
        """
        self.__getLastOrderState()
        self.updateCurrentTable()
    
    def __getLastOrderState(self):
        if len(self._executions) <= 0:
            self._last_order = dict()
            self.txt_log.append("{}: No executions.".\
                                format(datetime.datetime.now().strftime(self._datetimeFmt_LOG)))
            return
        
        try:
            last_execution = self._executions[-1]
            child_order_acceptance_id = last_execution["child_order_acceptance_id"]
            params={
                "product_code":self._product_code,
                "child_order_acceptance_id":child_order_acceptance_id,
            }
            results = self._api.getchildorders(**params)
            if len(results) <= 0:
                self._last_order = dict()
                self.txt_log.append("{}: No order with id {}.".\
                                    format(datetime.datetime.now().strftime(self._datetimeFmt_LOG),
                                           child_order_acceptance_id))
                return
            
            result = results[0]
            if not isinstance(result, dict):
                self._last_order = dict()
                self.txt_log.append("{}: result from id {} has an unacceptable type = '{}'.".\
                                    format(datetime.datetime.now().strftime(self._datetimeFmt_LOG),
                                           child_order_acceptance_id, 
                                           type(result)))
                return
            if not "child_order_date" in result.keys():
                self._last_order = dict()
                self.txt_log.append("{}: No order with id {}.".\
                                    format(datetime.datetime.now().strftime(self._datetimeFmt_LOG),
                                           child_order_acceptance_id))
                return
        except Exception as ex:
            self.txt_log.append("@ getting orders:", ex)
            return
        
        try:
            for key in self.current_table_key:
                if key == "date":
                    self._last_order[key] = result["child_order_date"].split("T")[-1][:8]
                elif key == "state":
                    self._last_order[key] = result["child_order_state"]
                else:
                    self._last_order[key] = result[key]
        except KeyError as ex:
            self.txt_log.append("@ updating the last order:", ex)
            return
    
    @footprint
    @pyqtSlot()
    def getOrderInterest(self):
        """getOrderInterest(self) -> None
        """
        self.__getOrderInterest()
        self.updateCurrentTable()

    def __getOrderInterest(self):
        try:
            results = self._api.getpositions(product_code=self._product_code)
            if len(results) <= 0:
                self._order_interest = dict()
                self.txt_log.append("{}: No order interests.".\
                                    format(datetime.datetime.now().strftime(self._datetimeFmt_LOG)))
                return
            
            result = results[0]
            if not isinstance(result, dict):
                self._order_interest = dict()
                self.txt_log.append("{}: result has an unacceptable type = '{}'.".\
                                    format(datetime.datetime.now().strftime(self._datetimeFmt_LOG), 
                                        type(result)))
                return
            if not "open_date" in result.keys():
                self._order_interest = dict()
                self.txt_log.append("{}: No order interests.".\
                                    format(datetime.datetime.now().strftime(self._datetimeFmt_LOG)))
                return
        except Exception as ex:
            self.txt_log.append("@ getting the order interest:", ex)
            return
        
        try:
            for key in self.current_table_key:
                if key == "date":
                    self._order_interest[key] = result["open_date"].split("T")[-1][:8]
                elif key == "state":
                    self._order_interest[key] = result["leverage"]
                else:
                    self._order_interest[key] = result[key]
        except KeyError as ex:
            self.txt_log.append("@ updating the order interest:", ex)
            return
    
    @footprint
    def updateCurrentTable(self):
        """updateCurrentTable(self) -> None
        TODO: to change the widget from QTableWidget to QTableView
        """
        try:
            for ii, key in enumerate(self.current_table_key):
                lex = "" if self._last_exec.get(key) is None else self._last_exec.get(key)
                los = "" if self._last_order.get(key) is None else self._last_order.get(key)
                loi = "" if self._order_interest.get(key) is None else self._order_interest.get(key)
                col = [loi, lex, los]
                self.current_table.setItem(ii, 0, QTableWidgetItem(key))
                for jj in range(len(col)):
                    self.current_table.setItem(ii, jj + 1, QTableWidgetItem(str(col[jj])))
        except Exception as ex:
            self.txt_log.append("@ updating CurrentTable:", ex)
            
    
    @footprint
    @pyqtSlot()
    def cancelAllOrders(self):
        """cancelAllOrders(self) -> None
        """
        self._api.cancelallchildorders()
        self.txt_log.append("{}: All the order were cancelled.".\
                            format(datetime.datetime.now().strftime(self._datetimeFmt_LOG)))

    
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
        """startGettingDataThread(self) -> None
        """
        if not self._thread_getData.isRunning():
            print("start thread by timer.")
            self._thread_getData.start()
        else:
            print("Thread is running.")
    
    @footprint
    @pyqtSlot(object)
    def updateData(self, obj):
        """updateData(self, obj) -> None
        """
        mag = 20
        if obj is not None:
            try:
                # Health information
                health = obj["health"]
                self.health_info.setText(health["health"])
                self.state_info.setText(health["state"])

                # Board information
                market_data = obj["market_data"]
                if "timestamp" not in market_data.keys():
                    print("Failure in getting ticker.")
                    return
                self.label_best_ask_value.setText(str(market_data["best_ask"]))
                self.label_ltp_value.setText(str(market_data["ltp"]))
                self.label_best_bid_value.setText(str(market_data["best_bid"]))
                if self.chk_btcjpy.isChecked():
                    ltp = int(market_data["ltp"])
                    ltp_to_set = (ltp // mag + 1) * mag
                    self.txt_btcjpy.setText(str(ltp_to_set))
                
                # # Balance information
                # balance = obj["balance"]
                # jpy_amount = 0
                # btc_amount = 0
                # for currency in balance:
                #     if currency["currency_code"] == "JPY":
                #         jpy_amount = currency["amount"]
                #     elif currency["currency_code"] == "BTC":
                #         btc_amount = currency["amount"]
                # self.jpy_value.setText(str(jpy_amount))
                # self.btc_value.setText(str("{0:.5f}".format(btc_amount)))
                # self.tot_value.setText(str(jpy_amount + int(btc_amount * market_data["ltp"])))

                # Collateral information
                collateral = obj["collateral"]
                self.jpy_value.setText(str(collateral["collateral"]))
                self.btc_value.setText(str(collateral["open_position_pnl"]))
                self.tot_value.setText(str(collateral["require_collateral"]))
                    
            except Exception as ex:
                print(ex)
                return

    @footprint
    @pyqtSlot()
    def checkIsTimerStopped(self):
        """checkIsTimerStopped(self) -> None
        """
        if self.stopTimer:
            self._timer_getData.stop()
            # print("timer stopped.")
            self.stopTimer = False
            self.btn_start_ticker.setEnabled(True)
            self.btn_start_ticker.setText("Start")
            self.checkValidationOfOrder()

######################## Closing processes ########################
    @footprint
    def closeEvent(self, event):
        """closeEvent(self, event) -> None
        (override function)
        process on closing the main widget
        """
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
                self.deleteTempExecutions()
                event.accept()
            else:
                event.ignore()
        else:
            self.stopAllTimers()
            self.saveExecutions()
            self.deleteTempExecutions()

    @footprint
    def stopAllTimers(self):
        """stopAllTimers(self) -> None
        """
        if self._timer_getData.isActive():
            self._timer_getData.stop()
    
    @footprint
    def deleteTempExecutions(self):
        """deleteTempExecutions(self) -> None
        delete files including each temporary execution
        """
        if not self.__DEBUG:
            tmpfldr = os.path.join(os.path.dirname(__file__), "tmp")
            if os.path.exists(tmpfldr):
                flist = glob.glob(os.path.join(tmpfldr, "*"))
                for fpath in flist:
                    os.remove(fpath)

def main():
    app = QApplication([])
    mw = OrderBoard()
    mw.show()
    app.exec_()

if __name__ == "__main__":
    main()
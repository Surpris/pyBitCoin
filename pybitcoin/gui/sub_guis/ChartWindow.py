#! /usr/bin/python3
#-*- coding:utf-8 -*-

"""
ChartWindow.py
This file offers the following items:

* ChartWindow
"""
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QDialog, QGridLayout, QMenu, QWidget, QLabel, QLineEdit, QTextEdit
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt
# from PyQt5.QtChart import QChartView, QChart
import pyqtgraph as pg

import sys
sys.path.append("../")
from utils import make_groupbox_and_grid, make_pushbutton
from CustomGraphicsItem import CandlestickItem


class ChartWindow(QDialog):
    """ChartWindow class
    This class offers an window to draw candlesticks on.
    """

    def __init__(self, *args):
        """__init__(self, *args) -> None
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
        self._groupbox_title_font_size = 14
        self._spacing = 5
        self._window_color = "gray"

        self._count = 0
        # self._plot_width = 30
        self.DEBUG = True
    
    def initGui(self):
        # self.setAttribute(Qt.WA_DeleteOnClose)
        self.initMainGrid()
        # self.setMenuBar()

        if self.DEBUG:
            self.setWindowTitle("CandleStick(Emulate)")
        else:
            self.setWindowTitle("CandleStick")
        
        # Plot area
        self.glw = pg.GraphicsLayoutWidget()
        self.glw.resize(self._window_width - 20, self._window_width - 20)

        self.plot = self.glw.addPlot()
        self.plot.plot()
        
        self.grid.addWidget(self.glw, 0, 0)

        # Buttons in debug mode
        if self.DEBUG:
            group_debug, grid_debug = make_groupbox_and_grid(
                self, self._window_width - 20, self._window_width - 20,
                "DEBUG", self._groupbox_title_font_size, self._spacing
            )
            self.button1 = make_pushbutton(
                self, 40, 16, "Update", 14, method=self.update, color=None, isBold=False
            )
            grid_debug.addWidget(self.button1, 0, 0)
            self.grid.addWidget(group_debug, 1, 0)

        # self.grid.addWidget(group1, 0, 0)

        # self.setFixedSize(self.size())
        # plot(self.data.mean(axis=1), np.arange(self.data.shape[0]), clear=True)
        # self.candlesticks = QCandleStickSet()
    
    def initMainGrid(self):
        """ initMainWidget(self) -> None
        initialize the main widget and its grid.
        """
        self.resize(self._window_width, self._window_height)
        self.setStyleSheet("background-color:{};".format(self._window_color))
        self.grid = QGridLayout(self)
        self.grid.setSpacing(5)
        # self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "python.png")))
    
    def update(self):
        """update(self, data) -> None
        """
        data_ = np.array(self.data[self._count % len(self.data)])
        self._count += 1
        if self._count > len(self.data):
            data_[0] = self._count
        self.plot.addItem(CandlestickItem(data_))
    
    def setData(self, data):
        """setData(self, data) -> None
        """
        if isinstance(data, np.ndarray):
            data = np.array(data)
        self.data = data
        self._count = 0

def main():
    app = QApplication([])
    # app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "python.png")))
    mw = ChartWindow()
    data = [  ## fields are (time, open, close, min, max).
        (1., 10, 15, 5, 13),
        (2., 13, 20, 9, 17),
        (3., 17, 23, 11, 14),
        (4., 14, 19, 5, 15),
        (5., 15, 22, 8, 9),
        (6., 9, 16, 8, 15),
    ]
    mw.setData(data)
    mw.show()
    app.exec_()

if __name__ == "__main__":
    main()
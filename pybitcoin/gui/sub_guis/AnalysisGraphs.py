#! /usr/bin/python3
#-*- coding:utf-8 -*-

"""
AnalysisGraphs.py
This file offers the following items:

* AnalysisGraphs
"""

import numpy as np
from PyQt5.QtWidgets import QDialog, QGridLayout, QWidget, QLabel
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, pyqtSlot
import pyqtgraph as pg

import sys
sys.path.append("../")
import time

from utils import make_groupbox_and_grid, make_pushbutton, make_label
from utils import footprint

class AnalysisGraphs(QWidget):
    """AnalysisGraphs class
    This class offers an window to plot the results of analysis of OHLCV datasets.
    """

    def __init__(self, parent=None, name = "", **kwargs):
        """__init__(self, parent=None, name = "", **kwargs) -> None
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
        self._init_window_width = 200 # [pixel]
        self._init_window_height = 600 # [pixel]
        self._subplot_size = 100 # [pixel]
        self._font_size_groupbox_title = 11 # [pixel]
        self._font_size_label = 11

        self._color_stat = "#2FC4DF"

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

        if self.DEBUG:
            self.setWindowTitle("Analysis(Debug)")

        # Coordinate and Value of the mouse pointer.
        widget_coor_value = QWidget(self)
        widget_coor_value.resize(self._init_window_width, 30)
        grid_coor_value = QGridLayout(widget_coor_value)
        grid_coor_value.setSpacing(10)

        self.label_coor_value = make_label(
            self, "(NA, NA, 0.00e-00)", self._font_size_label, isBold=True, alignment=Qt.AlignRight
        )
        grid_coor_value.addWidget(self.label_coor_value, 0, 0)

        # graphs
        self.glw = pg.GraphicsLayoutWidget()

        ## benefit map
        self.plot_benefit = self.glw.addPlot(
            # axisItems={"bottom":self.iw_axBottom, "left":self.iw_axLeft}
        )
        self.plot_benefit.setAspectLocked(True)
        self.img_benefit = pg.ImageItem()
        self.plot_benefit.addItem(self.img_benefit)

        def mouseMoved(pos):
            try:
                coor = self.img_benefit.mapFromScene(pos)
                x, y = int(coor.x()), int(coor.y())
                if self.img_benefit.image is not None:
                    img = self.img_benefit.image
                    if 0 <= x <= img.shape[1] and 0 <= y <= img.shape[0]:
                        pass
                        self.label_coor_value.setText("({0}, {1}, {2:.2e})".format(x, y, img[y, x]))
            except IndexError:
                pass
            except Exception as ex:
                print(ex)
        
        self.img_benefit.scene().sigMouseMoved.connect(mouseMoved)

        ## Box plot diagram for dead cross
        self.glw.nextRow()
        self.plot_box_dead = self.glw.addPlot()

        ## Box plot diagram for golden cross
        self.glw.nextRow()
        self.plot_box_golden = self.glw.addPlot()

        # construct
        grid.addWidget(widget_coor_value, 0, 0, 1, 1)
        grid.addWidget(self.glw, 1, 0, 1, 9)
    
    @pyqtSlot(object)
    def updateGraphs(self, obj):
        """updateGraphs(self, obj) -> None
        update graphs

        Parameters
        ----------
        obj : dict
            obj must have the following key-value pairs:
                benefit_map     : numpy.2darray
                N_dec           : int
                stat_dead       : numpy.2darray with the shape of (2**N_dec, 5)
                stat_golden     : numpy.2darray with the shape of (2**N_dec, 5)
                dec_dead_list   : list of numpy.1darrays with the length of 2**N_dec
                dec_golden_list : list of numpy.1darrays with the length of 2**N_dec
        """
        try:
            if not isinstance(obj, dict):
                print("The given object is not a dict object.")
                return
            self.img_benefit.setImage(obj["benefit_map"])

            self.plot_box_dead.clear()
            self.plot_box_dead.plot(
                np.arange(2**obj["N_dec"]), obj["stat_dead"][:, 2],
                clear=False, pen=pg.mkPen(self._color_stat, width=2)
            )

            self.plot_box_golden.clear()
            self.plot_box_golden.plot(
                np.arange(2**obj["N_dec"]), obj["stat_golden"][:, 2],
                clear=False, pen=pg.mkPen(self._color_stat, width=2)
            )
        except Exception as ex:
            print(ex)
            
    @footprint
    def plotInDebugMode(self):
        if not self.DEBUG:
            raise Exception("`plotInDebugMode` is supported only in the debug mode.")
        N_dec = 5
        benefit_map = np.random.uniform(0, 1., (10, 10))
        dec_golden_list = []
        dec_dead_list = []
        for ii in range(2**N_dec):
            dec_dead_list.append(np.random.uniform(-1., 0., 100))
            dec_golden_list.append(np.random.uniform(0., 1., 100))
        
        stat_dead = np.random.uniform(-1., 0., (2**N_dec, 5))
        stat_golden = np.random.uniform(0, 1., (2**N_dec, 5))
        for ii in range(2**N_dec):
            arr = dec_dead_list[ii]
            stat_dead[ii] = np.array([arr.max(), arr.min(), arr.mean(), arr.std(), np.median(arr)])
            arr = dec_golden_list[ii]
            stat_golden[ii] = np.array([arr.max(), arr.min(), arr.mean(), arr.std(), np.median(arr)])
        obj = {
            "N_dec":N_dec, "benefit_map":benefit_map, 
            "dec_dead_list":dec_dead_list, "dec_golden_list":dec_golden_list, 
            "stat_dead":stat_dead, "stat_golden":stat_golden
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
    mw = AnalysisGraphs()
    mw.show()
    mw.DEBUG = True
    mw.plotInDebugMode()
    app.exec_()

if __name__ == "__main__":
    main()
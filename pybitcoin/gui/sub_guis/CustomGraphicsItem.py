#! /usr/bin/python3
#-*- coding:utf-8 -*-

"""
Downloaded from https://groups.google.com/forum/#!topic/pyqtgraph/uJ_jJLln_3E
"""

import numpy as np
import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui

class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data):
        pg.GraphicsObject.__init__(self)
        self.data = np.array(data)  ## data must have fields: time, open, close, min, max
        self.generatePicture()
    
    def generatePicture(self):
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('w'))
        if len(self.data.shape) == 1:
            w = 1./3.
            t_, open_, high_, low_, close_ = self.data[:]
            p.drawLine(QtCore.QPointF(t_, low_), QtCore.QPointF(t_, high_))
            if open_ > close_:
                p.setBrush(pg.mkBrush('r'))
            else:
                p.setBrush(pg.mkBrush('g'))
            p.drawRect(QtCore.QRectF(t_-w, open_, w*2, close_-open_))
        else:
            w = (self.data[1][0] - self.data[0][0]) / 3.
            for (t, open, max, min, close) in self.data:
                p.drawLine(QtCore.QPointF(t, min), QtCore.QPointF(t, max))
                if open > close:
                    p.setBrush(pg.mkBrush('r'))
                else:
                    p.setBrush(pg.mkBrush('g'))
                p.drawRect(QtCore.QRectF(t-w, open, w*2, close-open))
        p.end()
    
    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())

if __name__ == "__main__":
    data = [  ## fields are (time, open, close, min, max).
        (1., 10, 15, 5, 13),
        (2., 13, 20, 9, 17),
        (3., 17, 23, 11, 14),
        (4., 14, 19, 5, 15),
        (5., 15, 22, 8, 9),
        (6., 9, 16, 8, 15),
    ]
    item = CandlestickItem(data)
    plt = pg.plot()
    plt.addItem(item)

    QtGui.QApplication.exec_()
#! /usr/bin/python3
#-*- coding:utf-8 -*-

"""
Downloaded from https://groups.google.com/forum/#!topic/pyqtgraph/uJ_jJLln_3E
"""

import numpy as np
import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui

class CandlestickItem(pg.GraphicsObject):
    """CandlestickItem(pg.GraphicsObject)

    This class offers graphic objecs of candlesticks
    """
    def __init__(self, data):
        """__init__(self, data) -> None
        
        initialize this class

        Parameters
        ----------
        data : list of tuples
            Each tuples has the following format:
            (timestamp, open, high, low, close)
        """
        pg.GraphicsObject.__init__(self)
        self.data = np.array(data)
        try:
            self.generatePicture()
        except Exception as ex:
            print(ex)
    
    def generatePicture(self):
        """generatePicture(self) -> None

        generate items for candlesticks
        """
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
        elif self.data.shape[0] == 1:
            w = 1./3.
            t_, open_, high_, low_, close_ = self.data[0, :]
            p.drawLine(QtCore.QPointF(t_, low_), QtCore.QPointF(t_, high_))
            if open_ > close_:
                p.setBrush(pg.mkBrush('r'))
            else:
                p.setBrush(pg.mkBrush('g'))
            p.drawRect(QtCore.QRectF(t_-w, open_, w*2, close_-open_))
        else:
            w = (self.data[1][0] - self.data[0][0]) / 3.
            for (t, open_, max_, min_, close_) in self.data:
                p.drawLine(QtCore.QPointF(t, min_), QtCore.QPointF(t, max_))
                if open_ > close_:
                    p.setBrush(pg.mkBrush('r'))
                else:
                    p.setBrush(pg.mkBrush('g'))
                p.drawRect(QtCore.QRectF(t-w, open_, w*2, close_-open_))
        p.end()
    
    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())

class BoxPlotItem(pg.GraphicsObject):
    """BoxPlotItem(pg.GraphicsObject)

    This class offers graphic objects of box plot.
    """
    def __init__(self, data):
        """__init__(self, data) -> None
        
        initialize this class

        Parameters
        ----------
        data : list of tuples
            Each tuple has the following format:
            (timestamp, 
             outliers, 
             lower whisker, 
             first quartile, 
             median, 
             third quartile, 
             upper whisker)
        """
        pg.GraphicsObject.__init__(self)
        self.data = data
        try:
            self.generatePicture()
        except Exception as ex:
            print(ex)
    
    def generatePicture(self):
        """generatePicture(self) -> None

        generate items for box plot
        """
        self.picture = QtGui.QPicture()
        self.p = QtGui.QPainter(self.picture)
        self.p.setPen(pg.mkPen('#FFFFFF'))
        for row in self.data:
            self.draw(row)
        self.p.end()
    
    def draw(self, data, width=1./3.):
        """draw(self, data, width=1./3.) -> None
        draw an item of box plot
        """
        t_, out, low_w, q1, q2, q3, up_w = data[:]
        self.p.drawLine(QtCore.QPointF(t_, low_w), QtCore.QPointF(t_, up_w))
        self.p.drawLine(QtCore.QPointF(t_ - width, low_w), QtCore.QPointF(t_ + width, low_w))
        self.p.drawLine(QtCore.QPointF(t_ - width, up_w), QtCore.QPointF(t_ + width, up_w))
        for out_ in out:
            self.p.drawEllipse(QtCore.QPointF(t_, out_), width, width)
        self.p.setBrush(pg.mkBrush("#000000"))
        self.p.drawRect(QtCore.QRectF(t_ - width, q1, width * 2, q3 - q1))
        self.p.setBrush(pg.mkBrush("#FFFFFF"))
        self.p.drawLine(QtCore.QPointF(t_ - width, q2), QtCore.QPointF(t_ + width, q2))
    
    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())

if __name__ == "__main__":
    app = QtGui.QApplication([])
    try:
        glw = pg.GraphicsLayoutWidget()

        data = [  ## fields are (time, open, close, min, max).
            (1., 10, 15, 5, 13),
            (2., 13, 20, 9, 17),
            (3., 17, 23, 11, 14),
            (4., 14, 19, 5, 15),
            (5., 15, 22, 8, 9),
            (6., 9, 16, 8, 15),
        ]
        item = CandlestickItem(data)
        plt = glw.addPlot()
        plt.addItem(item)
        def dataset_for_boxplot(arr, k=0):
            if not isinstance(arr, np.ndarray):
                arr = np.array(arr)
            q1 = np.percentile(arr, 25)
            q2 = np.median(arr)
            q3 = np.percentile(arr, 75)
            IQR = q3 - q1
            ind = (arr >= q1 - 1.5 * IQR) & (arr <= q3 + 1.5 * IQR)
            outliers = arr[~ind]
            lower_whisker = arr[ind].min()
            upper_whisker = arr[ind].max()
            return (k, outliers, lower_whisker, q1, q2, q3, upper_whisker)

        data = []
        for ii in range(32):
            a = np.random.randint(-10, 100)
            sample = np.random.uniform(a, a + 50, 100)
            sample = np.append(sample, np.random.uniform(100, 300))
            sample = np.append(sample, np.random.uniform(-200, -100))
            item_ = dataset_for_boxplot(sample, ii + 1)
            data.append(item_)
        glw.nextRow()
        item2 = BoxPlotItem(data)
        plt2 = glw.addPlot()
        plt2.addItem(item2)
        glw.show()
    except Exception:
        raise
    app.exec_()
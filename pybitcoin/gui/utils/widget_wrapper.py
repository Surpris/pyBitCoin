# -*- coding: utf-8 -*

from PyQt5 import  QtCore, QtGui, QtWidgets

def make_groupbox_and_grid(parent, width, height, title, fontsize, spacing):
    """make_groupbox_and_grid(parent, width, height, title, fontsize, spacing) -> groupbox, grid

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
    groupbox : QtWidgets.QGroupBox
    grid : QtWidgets.QGridLayout
    """

    groupbox = QtWidgets.QGroupBox(parent)
    groupbox.setTitle(title)
    font = groupbox.font()
    font.setPointSize(fontsize)
    groupbox.setFont(font)
    groupbox.resize(width, height)
    grid = QtWidgets.QGridLayout(groupbox)
    grid.setSpacing(spacing)
    return groupbox, grid

def make_label(parent, text, fontsize, isBold=False, alignment=None, color=None):
    """make_label(parent, text, fontsize, isBold, alignment, color) -> QLable

    Parameters
    ----------
    parent : parent class overtaking QtWidgets
    text : str
    fontsize : int
    isBold : bool
    alignment : QtCore.Qt.Align
    color : str (color code)

    Returns
    -------
    label : QtWidgets.QLabel
    """

    label = QtWidgets.QLabel(parent)
    label.setText(text)
    font = label.font()
    font.setPointSize(fontsize)
    font.setBold(isBold)
    label.setFont(font)
    
    if alignment is not None:
        label.setAlignment(alignment)
    if color is not None:
        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Foreground, QtGui.QColor(color))
        label.setPalette(pal)
    return label

def make_pushbutton(parent, width, height, text, fontsize, method=None, color=None, isBold=False):
    """make_pushbutton(parent, width, height, text, fontsize, method, color, isBold) -> QtWidgets.QPushButton

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
    button : QtWidgets.QPushButton

    """
    # clear button
    button = QtWidgets.QPushButton(parent)
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

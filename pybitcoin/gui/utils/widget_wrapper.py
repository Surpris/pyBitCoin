#! /usr/bin/python3
# -*- coding: utf-8 -*

from PyQt5 import  QtCore, QtGui, QtWidgets

def make_groupbox_and_grid(parent, width, height, title, fontsize, spacing):
    """make_groupbox_and_grid(parent, width, height, title, fontsize, spacing) -> QGroupBox, QGridLayout

    create a QGroupBox and QGridLayout
    
    Parameters
    ----------
    parent : parent class overtaking QtWidgets
        parent
    width : int
        width of a group box
    height : int
        height of the group box
    title : str
        title of the group box
    fontsize : int
        font size of the title
    spacing : int
        spacing of a grid in the group box
    
    Returns
    -------
    groupbox : QtWidgets.QGroupBox
        a group box
    grid : QtWidgets.QGridLayout
        a grid in the group box
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
    """make_label(parent, text, fontsize, isBold, alignment, color) -> QLabel

    create a QLabel instance

    Parameters
    ----------
    parent : parent class overtaking QtWidgets
        parent
    text : str
        text in a label
    fontsize : int
        font size of the text
    isBold : bool
        if True, then the text gets bold
    alignment : QtCore.Qt.Align
        alignment of the text
    color : str (color code)
        color of the text
    
    Returns
    -------
    label : QtWidgets.QLabel
        a label
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
    
    create a QPushBUtton instance

    Parameters
    ----------
    parent : class overtaking QtWidgets
        parent
    width : int
        width of a push button
    height : int
        height of the push button
    text : str
        text on the push button
    fontsize : str
        font size of the text
    method : function
        method to call when the button is clicked
    color : str (color code)
        color of the text
    isBold : bool
        if True, then the text gets bold

    Returns
    -------
    button : QtWidgets.QPushButton
        a push button
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

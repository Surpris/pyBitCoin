#! /usr/bin/python3
#-*- coding: utf-8 -*-

__author__ = "Toshiyuki Nishiyama"
__version__ = "0.1"

try:
    __PYBITCOIN__SETUP__
except NameError:
    __PYBITCOIN__SETUP__ = False

if __PYBITCOIN__SETUP__:
    import sys as _sys
    _sys.stderr.write('Running from pybitcoin source directory.\n')
    del _sys
else:
    # from . import backtest
    from . import core
    from . import gui
    from . import blockchain
    # from . import SQLDBclass
    # from . import MLClass

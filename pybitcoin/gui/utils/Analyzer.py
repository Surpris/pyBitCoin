#-*- coding: utf-8 -*-

import numpy as np
import pandas as pd
# from .mathfunctions import calc_EMA, find_cross_points, peakdet, symbolize

class Analyzer(object):
    """Analyzer(object)
    
    This class offers functions to calculate existent technical indices.
    In coming future, this offers 'my functions'.

    Examples
    --------
    >>> import numpy as np
    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> analyzer = Analyser()
    >>> timestamp = np.arange(1, 100)
    >>> ohlc = []
    >>> close = []
    >>> ema = []
    >>> N = 3
    >>> alpha = 2. / (1. + N)
    >>> for ii in range(len(timestamp)):
    ...     buff = np.zeros(5, dtype=int)
    ...     buff[0] = ii + 1
    ...     buff[1:] = np.random.randint(100, 150, 4)
    ...     ohlc.append(buff)
    ...     close.append(buff[-1])
    ...     ema.append(analyzer.calcEMA(close))
    ...
    >>> plt.plot(timestamp, close)
    >>> plt.plot(timestamp, ema)
    """
    def __init__(self):
        pass
    
    def calcDec(self, oc_up_down, N_dec=5):
        """calcDec(self, oc_up_down, N_dec=5) -> int

        calculate the decimal value for the corresponding pattern

        Parameters
        ----------
        oc_up_down : array-like
            list of 0-or-1 values
        N_dec      : int (default : int)
            the number of values to convert altogher into a decimal
        
        Returns
        -------
        a decimal corresponding to a pattern
        """
        if len(oc_up_down) > N_dec:
            return 0
        else:
            return int("".join([str(i_) for i_ in oc_up_down[-N_dec:]]), 2)
    
    def calcEMA(self, ema, base, alpha, ii=-1):
        """calcEMA(self, ema, base, alpha, ii=-1) -> float

        calculate the EMA value for the latest data in `base`

        Parameters
        ----------
        ema   : array-like
            list of historical EMA values
        base  : array-like
            list of historical values
        alpha : float
            alpha parameter of EMA calculation
        ii    : int (default : -1)
            index of the value in base used to calulate EMA
        
        Returns
        -------
        current EMA value
        """
        if len(ema) == 0:
            return 1 * base[0]
        else:
            return (1. - alpha) * ema[-1] + alpha * base[ii]
    
    def calcMACD(self, ema1, ema2):
        """calcMACD(self, ema1, ema2) -> float

        calculate the MACD value

        Parameters
        ----------
        ema1 : array-like
            the first EMA
        ema2 : array-like
            the second EMA
        
        Returns
        -------
        MACD : float
            current MACD value
        """
        if len(ema1) == 0 or len(ema2) == 0:
            return 0.
        else:
            return ema1[-1] - ema2[-1]
    
    def calcMACDSignal(self, signal, MACD, alpha, ii=-1):
        """calcMACDSignal(self, signal, MACD, alpha, ii=-1) -> float

        calculate the MACD signal

        Parameters
        ----------
        signal : array-like
            list of MACD signal
        MACD   : array-like
            list of historical EMA values
        alpha  : float
            alpha parameter of EMA calculation
        ii     : int (default : -1)
            index of the value in MACD used to calulate MACD signal
        
        Returns
        -------
        the current MACD signal (float)
        """
        return self.calcEMA(signal, MACD, alpha, ii)
    
    def calcTR(self, tohlc):
        """calcTR(self, tohlc) -> int

        calculate the current true range

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)

        Returns
        -------
        the current true range
        """
        if len(tohlc) == 0:
            return 0
        elif len(tohlc) == 1:
            return tohlc[-1][2] - tohlc[-1][3]
        else:
            return max([tohlc[-1][2]- tohlc[-1][3], tohlc[-1][2] - tohlc[-2][-1], tohlc[-2][-1] - tohlc[-1][3]])
    
    def calcATR(self, ATR, true_range, alpha, ii=-1):
        """calcATR(self, ATR, true_range, alpha, ii=-1) -> float

        calculate the current ATR value

        Parameters
        ----------
        ATR        : array-like
            list of ATR
        true_range : array-like
            list of true range
        alpha      : float
            alpha parameter for calculation of ATR
        ii         : int (default : -1)
            index

        Returns
        -------
        the current ATR value
        """
        return self.calcEMA(ATR, true_range, alpha, ii)
    
    def calcDMPlus(self, tohlc):
        """calcDMPlus(self, tohlc) -> int

        calculate the current DM+ value

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)

        Returns
        -------
        the current DM+ value
        """
        if len(tohlc) < 2:
            return 0
        else:
            HM = tohlc[-1][2] - tohlc[-2][2]
            LM = tohlc[-1][3] - tohlc[-2][3]
            if HM > LM and HM > 0:
                return HM
            else:
                return 0
    
    def calcDMMinus(self, tohlc):
        """calcDMMinus(self, tohlc) -> int

        calculate the current DM- value

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)

        Returns
        -------
        the urrent DM- value
        """
        if len(tohlc) < 2:
            return 0
        else:
            HM = tohlc[-1][2] - tohlc[-2][2]
            LM = tohlc[-1][3] - tohlc[-2][3]
            if HM < LM and LM > 0:
                return LM
            else:
                return 0
    
    def calcDMPlusEMA(self, DMPlusEMA, DMPlus, alpha, ii=-1):
        """calcDMPlusEMA(self, DMPlusEMA, DMPlus, alpha, ii=-1) -> float
        """
        return self.calcEMA(DMPlusEMA, DMPlus, alpha, ii)
    
    def calcDMMiusEMA(self, DMMinusEMA, DMMinus, alpha, ii=-1):
        """calcDMMiusEMA(self, DMMinusEMA, DMMinus, alpha, ii=-1) -> float
        """
        return self.calcEMA(DMMinusEMA, DMMinus, alpha, ii)

    def calcDIPlus(self, DMPlusEMA, ATR, alpha):
        """calcDIPlus(self, DMPlusEMA, ATR, alpha) -> float
        """
        return DMPlusEMA[-1] / ATR[-1] * 100.
    
    def calcDIMinus(self, DMMinusEMA, ATR, alpha):
        """calcDIMinus(self, DMMinusEMA, ATR, alpha) -> float
        """
        return DMMinusEMA[-1] / ATR[-1] * 100.
    
    def calcDX(self, DIPlus, DIMinus):
        """calcDX(self. DIPlus, DIMinus) > float
        """
        return np.abs(DIPlus[-1] - DIMinus[-1]) / (DIPlus[-1] + DIMinus[-1]) * 100.
    
    def calcADX(self, ADX, DX, alpha, ii=-1):
        """calcADX(self, ADX, DX, alpha, ii=-1) -> float
        """
        return self.calcEMA(ADX, DX, alpha, ii)
    
    def calcStd(self, tohlc):
        return 0.
    
    def calcRMS(self, tohlc):
        return 0.

    def calcBollingerBands(self, tohlc):
        return 0., 0., 0., 0., 0., 0.
    
    def calcMomentum(self, tohlc, n=1):
        if len(tohlc) < n + 1:
            raise ValueError("'n' must be smaller than the length of the 'tohlc' list.")
        return (tohlc[-1][-1] - tohlc[-n-1][-1]) / n
    

def main():
    for line in Analyzer.__doc__.split("\n"):
        print(line)

if __name__ == "__main__":
    main()
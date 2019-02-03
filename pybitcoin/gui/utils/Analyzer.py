#-*- coding: utf-8 -*-

import numpy as np
import pandas as pd
# from .mathfunctions import calc_EMA, find_cross_points, peakdet, symbolize

class TemporalAnalyzer(object):
    """TemporalAnalyzer(object)
    
    This class offers functions to calculate existent technical indices at the latest time.
    In coming future, this offers `my functions`.

    Examples
    --------
    >>> import numpy as np
    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> analyzer = TemporalAnalyzer()
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
        a decimal corresponding to a pattern (int)
        """
        if len(oc_up_down) > N_dec:
            return 0
        else:
            return int("".join([str(i_) for i_ in oc_up_down[-N_dec:]]), 2)
    
    def calcEMA(self, ema, base, alpha, ii=-1):
        """calcEMA(self, ema, base, alpha, ii=-1) -> float

        calculate the EMA value for the value in `base` identified by `ii`

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
        the current EMA value (float)
        """
        if len(ema) == 0:
            return 1 * base[ii]
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
            current MACD value (float)
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
    
    def calcTrueRange(self, tohlc):
        """calcTrueRange(self, tohlc) -> int

        calculate the current true range

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)

        Returns
        -------
        the current true range (float)
        """
        if len(tohlc) == 0:
            return 0
        elif len(tohlc) == 1:
            return tohlc[-1][2] - tohlc[-1][3]
        else:
            return max([tohlc[-1][2]- tohlc[-1][3], tohlc[-1][2] - tohlc[-2][-1], tohlc[-2][-1] - tohlc[-1][3]])
    
    def calcAverageTrueRange(self, ATR, true_range, alpha, ii=-1):
        """calcAverageTrueRange(self, ATR, true_range, alpha, ii=-1) -> float

        calculate the ATR value for the value in `true_range` identified by `ii`

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
        ATR value (float)
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
        the current DM+ value (float)
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
        the current DM- value (float)
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
        """calcMomentum(self, tohlc, n=1) -> float

        calculate the current momentum

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        n     : int (default : 1)
            the number of days to go back
        
        Returns
        -------
        the current momentum (float)
        """
        if len(tohlc) < n + 1:
            return 0.
        else:
            return (tohlc[-1][-1] - tohlc[-n-1][-1]) / n

    def calcROC1(self, tohlc, n=1):
        """calcROC1(self, tohlc, n=1) -> float

        calculate the current ROC Type.I

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        n     : int (default : 1)
            the number of days to go back
        
        Returns
        -------
        the current ROC Type.I (float)
        """
        if len(tohlc) < n + 1:
            return 0.
        else:
            return (tohlc[-1][-1] - tohlc[-n-1][-1]) / tohlc[-1][-1] * 100.
    
    def calcROC2(self, tohlc, n=1):
        """calcROC1(self, tohlc, n=1) -> float

        calculate the current ROC Type.II

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        n     : int (default : 1)
            the number of days to go back
        
        Returns
        -------
        the current ROC Type.II (float)
        """
        if len(tohlc) < n + 1:
            return 0.
        else:
            return (tohlc[-1][-1] - tohlc[-n-1][-1]) / tohlc[-n-1][-1] * 100.
    
    def calcOCDownEMA(self, ema, tohlc, alpha, ii=-1):
        """calcOCDownEMA(self, ema, tohlc, alpha, ii=-1) -> float

        calculate the EMA value for OC-down patterns

        Parameters
        ----------
        ema   : array-like
            list of historical EMA values
        tohlc  : array-like
            list of (timestamp, open, high, low, close)
        alpha : float
            alpha parameter of EMA calculation
        ii    : int (default : -1)
            index of the value in tohlc used to calulate EMA
        
        Returns
        -------
        EMA value for OC-down patterns (float)
        """
        if tohlc[ii][2] > tohlc[ii][-1]:
                w = tohlc[ii][2] - tohlc[ii][-1]
        else:
            w = 0.
        if len(ema) == 0:
            return w
        else:
            return (1. - alpha) * ema[-1] + alpha * w
    
    def calcOCUpEMA(self, ema, tohlc, alpha, ii=-1):
        """calcOCDownEMA(self, ema, tohlc, alpha, ii=-1) -> float

        calculate the EMA value for OC-up patterns

        Parameters
        ----------
        ema   : array-like
            list of historical EMA values
        tohlc  : array-like
            list of (timestamp, open, high, low, close)
        alpha : float
            alpha parameter of EMA calculation
        ii    : int (default : -1)
            index of the value in tohlc used to calulate EMA
        
        Returns
        -------
        EMA value for OC-up patterns (float)
        """
        if tohlc[ii][2] < tohlc[ii][-1]:
                w = tohlc[ii][-1] - tohlc[ii][2]
        else:
            w = 0.
        if len(ema) == 0:
            return w
        else:
            return (1. - alpha) * ema[-1] + alpha * w

    def calcRSI(self, oc_down_ema, oc_up_ema, ii=-1):
        """calcRSI(self, oc_down_ema, oc_up_ema, ii=-1) -> float

        calculate the RSI value

        Parameters
        ----------
        oc_down_ema : array-like
            list of EMA of OC-downs
        oc_up_ema   : array-like
            list of EMA of OC-ups
        ii    : int (default : -1)
            index of the value used to calculate RSI
        
        Returns
        -------
        RSI value (float)
        """
        return oc_up_ema[ii] / (oc_down_ema[ii] + oc_up_ema[ii]) * 100.
    
    def calcWPrecentR(self, tohlc, n=1):
        """calcWPrecentR(self, tohlc, n=1) -> float

        calculate the current William's %R.

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        n     : int (default : 1)
            the number of days to go back
        
        Returns
        -------
        the current William's %R (flaoat)
        """
        if len(tohlc) < n + 1:
            return -50.
        else:
            highest = max([row[2] for row in tohlc[-n-1:]])
            lowest = min([row[3] for row in tohlc[-n-1:]])
            return (tohlc[-1][-1] - highest) / (highest - lowest) * 100.
        
    def calcRatioOfDeviation(self, target, base, ii=-1):
        """calcRatioOfDeviation(self, target, base, ii=-1) -> float

        calculate the ration of deviation of `target` from `base`

        Parameters
        ----------

        Returns
        -------
        ratio of deviation (%)
        """
        return (target[ii] - base[ii]) / base[ii] * 100.
    
    def calcBuyingPressure(self, tohlc):
        """calcBuyingPressure(self, tohlc) -> int

        calculate the current buying pressure

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)

        Returns
        -------
        the current buynig pressure (float)
        """
        if len(tohlc) == 0:
            return 0
        elif len(tohlc) == 1:
            return tohlc[-1][-1] - tohlc[-1][3]
        else:
            return tohlc[-1][-1] - min(tohlc[-1][3], tohlc[-2][-1])
    
    def calcUltimateOscillator(self, buying_pressure, true_range, N1=7, N2=14, N3=28):
        """calcUltimateOscillator(self, buying_pressure, true_range, N1=7, N2=14, N3=28) -> float

        calculate the current ultimate oscillator

        Parameters
        ----------
        buying_pressure : array-like
            list of buying pressure
        true_range      : array-like
            list of true range
        N1              : int (default : 7)
            the first period
        N2              : int (default : 14)
            the second period
        N3              : int (default : 28)
            the third period
        
        Returns
        -------
        the current ultimate oscillator (float)
        """
        if len(buying_pressure) < N1 or len(true_range) < N1:
            avg1 = 0.5
        else:
            avg1 = np.sum(buying_pressure[-N1:]) / np.sum(true_range[-N1:])
        
        if len(buying_pressure) < N2 or len(true_range) < N2:
            avg2 = 0.5
        else:
            avg2 = np.sum(buying_pressure[-N2:]) / np.sum(true_range[-N2:])
        
        if len(buying_pressure) < N3 or len(true_range) < N3:
            avg3 = 0.5
        else:
            avg3 = np.sum(buying_pressure[-N3:]) / np.sum(true_range[-N3:])
        
        return (N1 * avg1 + N2 * avg2 + N3 * avg3) / (N1 + N2 + N3) * 100.

def main():
    for line in TemporalAnalyzer.__doc__.split("\n"):
        print(line)

if __name__ == "__main__":
    main()
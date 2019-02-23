#-*- coding: utf-8 -*-

import numpy as np
# import pandas as pd

class TemporalAnalyzer(object):
    """TemporalAnalyzer(object)
    
    This class offers functions to calculate existent technical indicators at the latest time.
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
    ...     ema.append(analyzer.calcEMA(ema, close, alpha))
    ...
    >>> plt.plot(timestamp, close)
    >>> plt.plot(timestamp, ema)
    """
    def __init__(self):
        pass
    
    def calcOcUpDown(self, tohlc, ii=-1):
        """calcOcUpDown(self, tohlc, ii=-1) -> int

        calculate a value to specify up/down of close

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        ii    : int (default : -1)
            index of tohlc to calculate the result with
            
        Returns
        -------
        oc_up_down : int
            if close > open then 1, otherwise 0
        """
        return int(tohlc[ii][-1] > tohlc[ii][2])
    
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

    def calcSMA(self, base, N, ii=-1):
        """calcSMA(self, base, alpha, ii=-1) -> float

        calculate the SMA value for the value in `base` (identified by `ii`)
        TODO: support the use of `ii`

        Parameters
        ----------
        base  : array-like
            list of historical values
        N : float
            the number of points to calculate SMA with
        ii    : int (default : -1)
            index of the value in base used to calulate SMA
        
        Returns
        -------
        the current SMA value (float)
        """
        if len(base) < N:
            return  np.mean(base)
        else:
            return np.mean(base[-N:])

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
            LM = tohlc[-2][3] - tohlc[-1][3]
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
            LM = tohlc[-2][3] - tohlc[-1][3]
            if HM < LM and LM > 0:
                return LM
            else:
                return 0
    
    def calcDMPlusEMA(self, DMPlusEMA, DMPlus, alpha, ii=-1):
        """calcDMPlusEMA(self, DMPlusEMA, DMPlus, alpha, ii=-1) -> float
        """
        return self.calcEMA(DMPlusEMA, DMPlus, alpha, ii)
    
    def calcDMMinusEMA(self, DMMinusEMA, DMMinus, alpha, ii=-1):
        """calcDMMinusEMA(self, DMMinusEMA, DMMinus, alpha, ii=-1) -> float
        """
        return self.calcEMA(DMMinusEMA, DMMinus, alpha, ii)

    def calcDIPlus(self, DMPlusEMA, ATR):
        """calcDIPlus(self, DMPlusEMA, ATR) -> float
        """
        return DMPlusEMA[-1] / ATR[-1] * 100.
    
    def calcDIMinus(self, DMMinusEMA, ATR):
        """calcDIMinus(self, DMMinusEMA, ATR) -> float
        """
        return DMMinusEMA[-1] / ATR[-1] * 100.
    
    def calcDX(self, DIPlus, DIMinus, threshold=30.):
        """calcDX(self. DIPlus, DIMinus, threshold=30.) > float
        """
        if DIPlus[-1] + DIMinus[-1] == 0.:
            return threshold
        else:
            return np.abs(DIPlus[-1] - DIMinus[-1]) / (DIPlus[-1] + DIMinus[-1]) * 100.
    
    def calcADX(self, ADX, DX, alpha, ii=-1):
        """calcADX(self, ADX, DX, alpha, ii=-1) -> float
        """
        return self.calcEMA(ADX, DX, alpha, ii)
    
    def calcRMSError(self, close, base, n=1):
        """calcRMSError(self, close, base, n=1) -> float

        calculate the current rms of error between `close` and `base`.

        Parameters
        ----------
        close : array-like
            list of close values
        base  : array-like
            list of base values (e.g. SMA, EMA)
        n     : int (default : 1)
            the number of days to consider
        
        Returns
        -------
        the current rms of error (float)
        """
        if len(base) < n:
            return np.std(np.array(close) - np.array(base))
        else:
            return np.std(np.array(close[-n:]) - np.array(base[-n:]))

    def calcBollingerBands(self, close, base, n=1):
        """calcBollingerBands(self, close, base, n=1) -> 7 floats

        calculate the current values for Bollinger bands

        Parameters
        ----------
        close : array-like
            list of close values
        base  : array-like
            list of base values (e.g. SMA, EMA)
        n     : int (default : 1)
            the number of days to consider
        
        Returns
        -------
        the current values for Bollinger bands (7 floats)
        """
        sigma = self.calcRMSError(close, base, n)
        return close[-1] - 3. * sigma, close[-1] - 2. * sigma, close[-1] - sigma, close[-1], \
               close[-1] + sigma, close[-1] + 2. * sigma, close[-1] + 3. * sigma
    
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
        if tohlc[ii][1] > tohlc[ii][-1]:
            w = tohlc[ii][1] - tohlc[ii][-1]
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
        if tohlc[ii][1] < tohlc[ii][-1]:
            w = tohlc[ii][-1] - tohlc[ii][1]
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
    
    def calcWPercentR(self, tohlc, n=1):
        """calcWPercentR(self, tohlc, n=1) -> float

        calculate the current William's %R.

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        n     : int (default : 1)
            the number of days to consider
        
        Returns
        -------
        the current William's %R (flaoat)
        """
        if len(tohlc) < n:
            return -50.
        else:
            highest = max([row[2] for row in tohlc[-n:]])
            lowest = min([row[3] for row in tohlc[-n:]])
            return (tohlc[-1][-1] - highest) / (highest - lowest) * 100.
        
    def calcRatioOfDeviation(self, target, base, ii=-1):
        """calcRatioOfDeviation(self, target, base, ii=-1) -> float

        calculate the ratio of deviation of `target` from `base`

        Parameters
        ----------
        target : array-like
            list of target values
        base  : array-like
            list of base values (e.g. close)

        Returns
        -------
        ratio of deviation (%)
        """
        return (target[ii] - base[ii]) / base[ii] * 100.
    
    def calcUltimateOscillator(self, buying_pressure, true_range, N1=7, N2=14, N3=28):
        """calcUltimateOscillator(self, buying_pressure, true_range, N1=7, N2=14, N3=28) -> float

        calculate the current ultimate oscillator (UO)

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
        the current UO (float)
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
    
    def calcAwesomeOscillator(self, tohlc, N1=5, N2=34):
        """calcAwesomeOscillator(self, tohlc, N1=5, N2=34) -> float

        calculate the current awesome oscillator (AO)

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        N1    : int (default : 5)
            the first period
        N2    : int (default : 34)
            the second period
        
        Returns
        -------
        the current AO (float)
        """
        if len(tohlc) < N1:
            base1 = [(row[2] + row[3]) / 2. for row in tohlc]
        else:
            base1 = [(row[2] + row[3]) / 2. for row in tohlc[-N1:]]

        if len(tohlc) < N2:
            base2 = [(row[2] + row[3]) / 2. for row in tohlc]
        else:
            base2 = [(row[2] + row[3]) / 2. for row in tohlc[-N2:]]
        
        return self.calcSMA(base1, N1) - self.calcSMA(base2, N2)
    
class Analyzer(object):
    """Analyzer(object)
    
    This class offers functions to calculate existent technical indicators.
    In coming future, this offers `my functions`.

    Examples
    --------
    >>> import numpy as np
    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> analyzer = Analyzer()
    >>> timestamp = np.arange(1, 100)
    >>> ohlc = []
    >>> close = []
    >>> N = 3
    >>> alpha = 2. / (1. + N)
    >>> for ii in range(len(timestamp)):
    ...     buff = np.zeros(5, dtype=int)
    ...     buff[0] = ii + 1
    ...     buff[1:] = np.random.randint(100, 150, 4)
    ...     ohlc.append(buff)
    ...     close.append(buff[-1])
    ...
    >>> ema = analyzer.calcEMA(close, alpha)
    >>> plt.plot(timestamp, close)
    >>> plt.plot(timestamp, ema)
    """
    pass

    def __init__(self):
        pass
    
    def calcOcUpDown(self, tohlc):
        """calcOcUpDown(self, tohlc) -> list

        calculate values to specify up/down of close

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
            
        Returns
        -------
        oc_up_down : list
            list of values to specify up/down of close.
            if close > open then 1, otherwise 0.
        """
        oc_up_down = [] 
        for row in tohlc:
            oc_up_down.append(int(row[-1] > row[2]))
        
        return oc_up_down
    
    def calcDec(self, oc_up_down, N_dec=5):
        """calcDec(self, oc_up_down, N_dec=5) -> list

        calculate the decimal value for the corresponding pattern

        Parameters
        ----------
        oc_up_down : array-like
            list of 0-or-1 values
        N_dec      : int (default : int)
            the number of values to convert altogher into a decimal
        
        Returns
        -------
        dec : list
            list of decimals corresponding to each pattern
        """
        dec = []
        for ii in range(len(oc_up_down)):
            if ii < N_dec - 1:
                dec.append(0)
            else:
                dec.append(int("".join([str(i_) for i_ in oc_up_down[ii-N_dec+1:ii+1]]), 2))
        
        return dec

    def calcSMA(self, base, N):
        """calcSMA(self, base, alpha) -> list

        calculate the SMA values

        Parameters
        ----------
        base  : array-like
            list of historical values
        N : float
            the number of periods
        
        Returns
        -------
        sma : list
            list of SMA values
        """
        if N == 1:
            return base[:]
        
        sma = []
        for ii in range(len(base)):
            if ii < N - 1:
                sma.append(np.mean(base[0:ii+1]))
            else:
                sma.append(np.mean(base[ii-N+1:ii+1]))
        
        return sma

    def calcEMA(self, base, alpha):
        """calcEMA(self, base, alpha) -> list

        calculate the EMA values

        Parameters
        ----------
        base  : array-like
            list of historical values
        alpha : float
            alpha parameter of EMA calculation
        
        Returns
        -------
        ema : list
            list of EMA values
        """
        ema = []
        for ii in range(len(base)):
            if ii == 0:
                ema.append(1 * base[0])
            else:
                ema.append((1. - alpha) * ema[-1] + alpha * base[ii])
        
        return ema

    def calcMACD(self, ema1, ema2):
        """calcMACD(self, ema1, ema2) -> list

        calculate the MACD value

        Parameters
        ----------
        ema1 : array-like
            the first EMA
        ema2 : array-like
            the second EMA
        
        Returns
        -------
        list of MACD
        """
        return [a - b for a, b in zip(ema1, ema2)]
    
    def calcMACDSignal(self, MACD, alpha):
        """calcMACDSignal(self, MACD, alpha) -> list

        calculate the MACD signals

        Parameters
        ----------
        MACD   : array-like
            list of historical EMA values
        alpha  : float
            alpha parameter of EMA calculation
        
        Returns
        -------
        list of MACD signals
        """
        return self.calcEMA(MACD, alpha)
    
    def calcBuyingPressure(self, tohlc):
        """calcBuyingPressure(self, tohlc) -> list

        calculate buying pressure

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)

        Returns
        -------
        bp : list
            list of buynig pressure
        """
        bp = []
        for ii in range(len(tohlc)):
            if ii == 0:
                bp.append(tohlc[ii][-1] - tohlc[ii][3])
            else:
                bp.append(tohlc[ii][-1] - min(tohlc[ii][3], tohlc[ii-1][-1]))
        
        return bp
        
    def calcTrueRange(self, tohlc):
        """calcTrueRange(self, tohlc) -> list

        calculate the current true range

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)

        Returns
        -------
        tr : list
            list of true range
        """
        tr = []
        for ii in range(len(tohlc)):
            if ii == 0:
                tr.append(tohlc[ii][2] - tohlc[ii][3])
            else:
                tr.append(
                    max([
                        tohlc[ii][2] - tohlc[ii][3], 
                        tohlc[ii][2] - tohlc[ii-1][-1], 
                        tohlc[ii-1][-1] - tohlc[ii][3]
                    ])
                )
        
        return tr
    
    def calcAverageTrueRange(self, true_range, alpha):
        """calcAverageTrueRange(self, true_range, alpha) -> list

        calculate the ATR values

        Parameters
        ----------
        true_range : array-like
            list of true range
        alpha      : float
            alpha parameter for calculation of ATR

        Returns
        -------
        list of ATR
        """
        return self.calcEMA(true_range, alpha)
    
    def calcDMPlus(self, tohlc):
        """calcDMPlus(self, tohlc) -> list

        calculate DM+

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)

        Returns
        -------
        dmp : list
            list of DM+
        """
        dmp = []
        for ii in range(len(tohlc)):
            if ii == 0:
                dmp.append(0)
            else:
                HM = tohlc[ii][2] - tohlc[ii-1][2]
                LM = tohlc[ii-1][3] - tohlc[ii][3]
                if HM > LM and HM > 0:
                    dmp.append(HM)
                else:
                    dmp.append(0)
        
        return dmp
    
    def calcDMMinus(self, tohlc):
        """calcDMMinus(self, tohlc) -> list

        calculate DM-

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)

        Returns
        -------
        dmm : list
            list of DM-
        """
        dmm = []
        for ii in range(len(tohlc)):
            if ii == 0:
                dmm.append(0)
            else:
                HM = tohlc[ii][2] - tohlc[ii-1][2]
                LM = tohlc[ii-1][3] - tohlc[ii][3]
                if HM < LM and LM > 0:
                    dmm.append(LM)
                else:
                    dmm.append(0)
        
        return dmm
    
    def calcDMPlusEMA(self, DMPlus, alpha):
        """calcDMPlusEMA(self, DMPlus, alpha) -> list
        """
        return self.calcEMA(DMPlus, alpha)
    
    def calcDMMinusEMA(self, DMMinus, alpha):
        """calcDMMinusEMA(self, DMMinus, alpha) -> list
        """
        return self.calcEMA(DMMinus, alpha)

    def calcDIPlus(self, DMPlusEMA, ATR):
        """calcDIPlus(self, DMPlusEMA, ATR) -> list
        """
        return [dmp / atr * 100. for dmp, atr in zip(DMPlusEMA, ATR)]
    
    def calcDIMinus(self, DMMinusEMA, ATR):
        """calcDIMinus(self, DMMinusEMA, ATR) -> list
        """
        return [dmm / atr * 100. for dmm, atr in zip(DMMinusEMA, ATR)]
    
    def calcDX(self, DIPlus, DIMinus, threshold=30.):
        """calcDX(self. DIPlus, DIMinus, threshold=30.) > list
        """
        dx = []
        for ii in range(len(DIPlus)):
            if DIPlus[ii] + DIMinus[ii] == 0.:
                dx.append(threshold)
            else:
                dx.append(np.abs(DIPlus[ii] - DIMinus[ii]) / (DIPlus[ii] + DIMinus[ii]) * 100.)
        
        return dx
    
    def calcADX(self, DX, alpha):
        """calcADX(self, ADX, DX, alpha, ii=-1) -> list
        """
        return self.calcEMA(DX, alpha)
    
    def calcRMSError(self, close, base, N=1):
        """calcRMSError(self, close, base, N=1) -> list

        calculate rms of error between `close` and `base`.

        Parameters
        ----------
        close : array-like
            list of close values
        base  : array-like
            list of base values (e.g. SMA, EMA)
        N     : int (default : 1)
            the number of days to consider
        
        Returns
        -------
        rms : list
            list of rms of error
        """
        rms = []
        for ii in range(len(base)):
            if ii < N - 1:
                rms.append(np.std(np.array(close[:ii+1]) - np.array(base[:ii+1])))
            else:
                rms.append(np.std(np.array(close[ii-N+1:ii+1]) - np.array(base[ii-N+1:ii+1])))
        
        return rms

    def calcBollingerBands(self, close, base, N=1):
        """calcBollingerBands(self, close, base, N=1) -> 7 lists

        calculate Bollinger bands

        Parameters
        ----------
        close : array-like
            list of close values
        base  : array-like
            list of base values (e.g. SMA, EMA)
        N     : int (default : 1)
            the number of days to consider
        
        Returns
        -------
        Bollinger bands
        """
        sigma = self.calcRMSError(close, base, N)
        m3sigma = []
        m2sigma = []
        m1sigma = []
        p1sigma = []
        p2sigma = []
        p3sigma = []
        for c, s in zip(close, sigma):
            m3sigma.append(c - 3. * s)
            m2sigma.append(c - 2. * s)
            m1sigma.append(c - s)
            p1sigma.append(c + s)
            p2sigma.append(c + 2. * s)
            p3sigma.append(c + 3. * s)
        
        return m3sigma, m2sigma, m1sigma, close, p1sigma, p2sigma, p3sigma
    
    def calcMomentum(self, tohlc, N=1):
        """calcMomentum(self, tohlc, N=1) -> list

        calculate momenta

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        N     : int (default : 1)
            the number of days to go back
        
        Returns
        -------
        M : list
            list of momenta
        """
        M = []
        for ii in range(len(tohlc)):
            if ii < N:
                M.append(0.)
            else:
                M.append((tohlc[ii][-1] - tohlc[ii-N][-1]) / N)
        
        return M

    def calcROC1(self, tohlc, N=1):
        """calcROC1(self, tohlc, N=1) -> list

        calculate ROC Type.I

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        N     : int (default : 1)
            the number of days to go back
        
        Returns
        -------
        roc : list 
            list of ROC Type.I
        """
        roc = []
        for ii in range(len(tohlc)):
            if ii < N:
                roc.append(0.)
            else:
                roc.append((tohlc[ii][-1] - tohlc[ii-N][-1]) / tohlc[ii][-1] * 100.)
        
        return roc
    
    def calcROC2(self, tohlc, N=1):
        """calcROC1(self, tohlc, N=1) -> list

        calculate ROC Type.II

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        N     : int (default : 1)
            the number of days to go back
        
        Returns
        -------
        roc : list
            list of ROC Type.II
        """
        roc = []
        for ii in range(len(tohlc)):
            if ii < N:
                roc.append(0.)
            else:
                roc.append((tohlc[ii][-1] - tohlc[ii-N][-1]) / tohlc[ii-N][-1] * 100.)
        
        return roc
    
    def calcOCDownEMA(self, tohlc, alpha):
        """calcOCDownEMA(self, tohlc, alpha) -> list

        calculate the EMA value for OC-down patterns

        Parameters
        ----------
        tohlc  : array-like
            list of (timestamp, open, high, low, close)
        alpha : float
            alpha parameter of EMA calculation
        
        Returns
        -------
        oc_down_ema : list
            list of EMA for OC-down patterns
        """
        oc_down_ema = []
        for ii in range(len(tohlc)):
            if tohlc[ii][1] > tohlc[ii][-1]:
                w = tohlc[ii][1] - tohlc[ii][-1]
            else:
                w = 0.
            if ii == 0:
                oc_down_ema.append(w)
            else:
                oc_down_ema.append((1. - alpha) * oc_down_ema[-1] + alpha * w)
        
        return oc_down_ema
    
    def calcOCUpEMA(self, tohlc, alpha):
        """calcOCDownEMA(self, tohlc, alpha) -> list

        calculate the EMA value for OC-up patterns

        Parameters
        ----------
        tohlc  : array-like
            list of (timestamp, open, high, low, close)
        alpha : float
            alpha parameter of EMA calculation
        
        Returns
        -------
        oc_up_ema : list
            list of EMA for OC-up patterns
        """
        oc_up_ema = []
        for ii in range(len(tohlc)):
            if tohlc[ii][1] < tohlc[ii][-1]:
                w = tohlc[ii][-1] - tohlc[ii][1]
            else:
                w = 0.
            if ii == 0:
                oc_up_ema.append(w)
            else:
                oc_up_ema.append((1. - alpha) * oc_up_ema[-1] + alpha * w)
        
        return oc_up_ema

    def calcRSI(self, oc_down_ema, oc_up_ema):
        """calcRSI(self, oc_down_ema, oc_up_ema) -> list

        calculate RSI

        Parameters
        ----------
        oc_down_ema : array-like
            list of EMA of OC-downs
        oc_up_ema   : array-like
            list of EMA of OC-ups
        
        Returns
        -------
        list of RSI
        """
        return [u / (u + d) * 100. for u, d in zip(oc_up_ema, oc_down_ema)]
    
    def calcWPercentR(self, tohlc, N=1):
        """calcWPercentR(self, tohlc, N=1) -> list

        calculate the current William's %R.

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        N     : int (default : 1)
            the number of days to consider
        
        Returns
        -------
        wpr : list
        list of William's %R
        """
        wpr = []
        for ii in range(len(tohlc)):
            if ii < N - 1:
                wpr.append(-50.)
            else:
                highest = max([row[2] for row in tohlc[ii-N+1:ii+1]])
                lowest = min([row[3] for row in tohlc[ii-N+1:ii+1]])
                wpr.append((tohlc[ii][-1] - highest) / (highest - lowest) * 100.)
        
        return wpr
        
    def calcRatioOfDeviation(self, target, base, ii=-1):
        """calcRatioOfDeviation(self, target, base, ii=-1) -> float

        calculate the ratio of deviation of `target` from `base`

        Parameters
        ----------
        target : array-like
            list of target values
        base  : array-like
            list of base values (e.g. close)

        Returns
        -------
        list of ratio of deviation (%)
        """
        return [(t - b) / b * 100. for t, b in zip(target, base)]
    
    def calcUltimateOscillator(self, buying_pressure, true_range, N1=7, N2=14, N3=28):
        """calcUltimateOscillator(self, buying_pressure, true_range, N1=7, N2=14, N3=28) -> float

        calculate ultimate oscillator (UO)

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
        list of UO
        """
        assert len(buying_pressure) == len(true_range), ValueError("no match length")
        uo = []
        for ii in range(len(buying_pressure)):
            if ii < N1 - 1:
                avg1 = 0.5
            else:
                avg1 = np.sum(buying_pressure[ii-N1+1:ii+1]) / np.sum(true_range[ii-N1+1:ii+1])
            if ii < N2 - 1:
                avg2 = 0.5
            else:
                avg2 = np.sum(buying_pressure[ii-N2+1:ii+1]) / np.sum(true_range[ii-N2+1:ii+1])
            if ii < N3 - 1:
                avg3 = 0.5
            else:
                avg3 = np.sum(buying_pressure[ii-N3+1:ii+1]) / np.sum(true_range[ii-N3+1:ii+1])
            uo.append((N1 * avg1 + N2 * avg2 + N3 * avg3) / (N1 + N2 + N3) * 100.)
        
        return uo
    
    def calcAwesomeOscillator(self, tohlc, N1=5, N2=34):
        """calcAwesomeOscillator(self, tohlc, N1=5, N2=34) -> float

        calculate awesome oscillator (AO)

        Parameters
        ----------
        tohlc : array-like
            list of (timestamp, open, high, low, close)
        N1    : int (default : 5)
            the first period
        N2    : int (default : 34)
            the second period
        
        Returns
        -------
        list of AO
        """
        base = [(row[2] + row[3]) / 2. for row in tohlc]
        first = self.calcSMA(base, N1)
        second = self.calcSMA(base, N2)
        return [f - s for f, s in zip(first, second)]

def main():
    for line in TemporalAnalyzer.__doc__.split("\n"):
        print(line)

if __name__ == "__main__":
    main()
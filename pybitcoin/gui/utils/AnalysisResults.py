#! /usr/bin/python3
# -*- coding: utf-8 -*-

"""
AnalysisResults.py
This file offers the following items:

* AnalysisResults
* InitializeError (used in this module)
* LoadAnalysisResultsError (used in this module)
"""

from datetime import datetime
import pandas as pd
import warnings

def define_property(self, name, field_level, value=None, readable=True, writable=True):
    """define_property(self, name, value=None, readable=True, writable=True) -> None
    
    define a property
    
    Parameters
    ----------
    self        : a class instance
        a class instance to define the property in
    name        : str
        name of the property
    field_level : str
        level of accessibility
    value       : object (default : None)
        initial value of the property
    readable    : bool (default : True)
        readability
    writable    : bool (default : True)
        writability
    """
    # define field_name
    if field_level not in ["internal", "private"]:
        raise ValueError("'field_level' must be in ['internal', 'private'].")
    if field_level == "internal":
        field_name = "_{}".format(name)
    elif field_level == "private":
        field_name = "_{}__{}".format(self.__class__.__name__, name)

    # set the initial value
    setattr(self, field_name, value)

    # define the property after generatind getter/setter
    getter = (lambda self: getattr(self, field_name)) if readable else None
    setter = (lambda self, value: setattr(self, field_name, value)) if writable else None
    setattr(self.__class__, name, property(getter, setter))

class LoadAnalysisResultsError(Exception):
    """LoadAnalysisResultsError(Exception)

    an exception class called when faiuring to load data of results of analysis
    """
    def __init__(self, expression=None, message=None):
        self.expression = expression
        self.message = message

class InitializeError(Exception):
    """InitializeError(Exception)

    an exception class called when faiuring initialization
    """
    def __init__(self, expression=None, message=None):
        self.expression = expression
        self.message = message

class AnalysisResults(object):
    """AnalysisResults(object)
    
    This class wraps pandas.DataFrae to handle the results of analysis.

    Examples
    --------
    >>> fpath = "/path/to/file.ext"
    >>> res = AnalysisResults(fpath)
    >>> import numpy as np
    >>> res.append(np.random.randint(0, 100, len(res.df.columns)))
    >>> res.save()
    """
    def __init__(self, results=None):
        """__init__(self, results=None) -> None
        
        initialize this class

        Parameters
        ----------
        results : str or pandas.DataFrame (default : None)
            if str then a path of results of analysis
            elif DataFrame then retuls of analysis
        """

        # set properties
        self._properties = [
            "oc_up_down", "dec", "ema1", "ema2", "ema3", "macd", "macd_signal",
            "buying_pressure", "true_range", "atr", 
            "dm_plus", "dm_minus", "dm_plus_ema", "dm_minus_ema", "di_plus", "di_minus", "dx", "adx",
            "std", "upper_band1", "upper_band2", "upper_band3", "lower_band1", "lower_band2", "lower_band3",
            "momentum", "roc1", "roc2", "ema_oc_up", "ema_oc_down", "rsi", "w_percent_r", "uo", "ao"
        ]
        self._save_datetime_fmt = "%Y%m%d%H%M%S"
        if results is not None:
            is_success = self.loadData(results)
            if not is_success:
                raise LoadAnalysisResultsError("Failure in loading a dataset from the given input.")    
        else:
            is_success = self.initParameters()
            if not is_success:
                raise InitializeError("Some error occurs in initialization.")
        
        # define properties
        define_property(self, "df", "internal", self._df, True, False)
        
    def initParameters(self):
        """initParameters(self) -> bool

        initialize the inner parameters

        Returns
        -------
        is_success : bool
            status of initialization
        """
        try:
            self._df = pd.DataFrame(columns=self._properties)
            return True
        except:
            return False
    
    def loadData(self, results):
        """loadData(self, results) -> bool

        load a dataset of rsults of analysis

        Parameters
        ----------
        results : str or pd.DataFrame
            if str then a path of results of analysis
            elif DataFrame then retuls of analysis
        
        Returns
        -------
        is_success : bool
            status of loading data
        """
        is_success = False
        if isinstance(results, str):
            try:
                buff = pd.read_csv(results)
                if sorted(list(buff.columns)) == sorted(self._properties):
                    self._df = buff
                    is_success = True
            except Exception as ex:
                print(ex)
                pass
        elif isinstance(results, pd.DataFrame):
            buff = results
            if sorted(list(buff.columns)) == sorted(self._properties):
                self._df = buff
                is_success = True
        return is_success
    
    def append(self, ary):
        """append(self, ary) -> bool

        append an array of results to the inner data

        Parameters
        ----------
        ary : array-like
            ary must have the dataset of analysis results with the same order of `_properties`.
        """
        is_success = False
        try:
            self._df.loc[len(self._df)] = ary
            is_success = True
        except ValueError as ex:
            print(ex)
        
        return is_success
    
    def save(self, fpath=None):
        """save(self, fpath=None) -> bool

        save the current results

        Parameters
        ----------
        fpath : str (default : None)
            a path of file to save the results to
        
        Returns
        -------
        is_success : bool
            status of save
        """
        is_success = False
        try:
            if fpath is None:
                fpath = "./{}".format(datetime.now().strftime(self._save_datetime_fmt))
                warnings.warn("'fpath' is not assigned. save the results to '{}'.",format(fpath))
            self._df.to_csv(fpath)
            is_success = True
        except Exception as ex:
            print(ex)
            pass
        return is_success

if __name__ == "__main__":
    print("test to use the AnalysisResults class")
    try:
        res = AnalysisResults()
        for line in res.__doc__.split("\n"):
            print(line)
        
        # res.save()
    except Exception:
        raise
    print("test to raise LoadAnalysisResultsError")
    try:
        raise LoadAnalysisResultsError
    except LoadAnalysisResultsError:
        print("success")
    
    print("test to raise InitializeError")
    try:
        raise InitializeError
    except InitializeError:
        print("success")
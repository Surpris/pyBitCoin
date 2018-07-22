#! /usr/bin/python3
# -*- coding: utf-8 -*-

import numpy as np
import pybitflyer
from PyQt5.QtCore import QMutex, QMutexLocker, pyqtSignal, QObject, pyqtSlot

from .Worker import Worker

class Bot1(Worker):
    """Bot1
    Bot class for OrderBoard
    """
    # do_something_bot = pyqtSignal(object)
    finished_bot = pyqtSignal()

    def __init__(self, name="", parent=None, api=None, 
                 product_code="FX_BTC_JPY", size=0.01, loss_cutting=0.0, profit_taking=0.0,
                 threshold=0.0, DEBUG=False):
        """__init__(self, *args, **kwargs) -> None
        initialize this class

        Parameters
        ----------
        name : str, optional (default : '')
        parent : QtWigdets or class overtaking QtWidgets, optional (default : None)
        api : pybitflyer.API, optional (default : None)
        product_code : str, optional (dafault : None)
        size : float, optional (default : 0.01)
        loss_cutting : float, optional (default : 0.0)
        profit_taking : float, optional (default : 0.0)
        threshold : float, optional (default : 0.0)
        DEBUG : bool, optional (default : False)
        """
        super().__init__(name=name, parent=parent)
        self._api = api
        self._product_code = product_code
        self.btc_size = size
        self._loss_cutting = loss_cutting
        self._profit_taking = profit_taking
        self._threshold = threshold
        self.__DEBUG = DEBUG

        self._cutting_ratio = 2.0
        self._order_condition = "MARKET"
        self._minute_to_expire = 10
        self._side = "WAIT" # state = "WAIT", "BUY", "SELL"
        self._tmp_side = "WAIT"
        
        self.init_data()
    
    @pyqtSlot()
    def init_data(self):
        self._tick_count_max = 5
        self._tick_count = 0
        self._ltp_list = []
        self._pnl_list = []
        self._execution_list = []
        self._accepted_jpy = None
        self._accepted_id = None
        self.data2 = None # ?
    
    @pyqtSlot(object)
    def process_bot(self, obj1):
        self.data = obj1
        if self.__DEBUG:
            print("bot: process_bot")
            print(self.data)
        # self.data2 = obj2
        try:
            with QMutexLocker(self.mutex):
                self._process()
        except Exception as ex:
            print(ex)
        # self.do_something_bot.emit(self.data)
        self.finished_bot.emit()
    
    def _process(self):
        # if self.data is None or self.data2 is None:
        if self.data is None:
            return
        try:
            # Board information
            market_data = self.data["market_data"]
            if "timestamp" not in market_data.keys():
                print("bot: failure in getting ticker.")
                return
            self._ltp_list.append(market_data["ltp"])
            collateral = self.data["collateral"]
            self._pnl_list.append(collateral["open_position_pnl"])
            self._tick_count += 1
            if self._tick_count > 0 and self._accepted_id is not None and self._accepted_jpy is None:
                if self.__DEBUG:
                    print("bot: getchildorders")
                    results = self._api.getchildorders(product_code=self._product_code)
                else:
                    results = self._api.getchildorders(product_code=self._product_code, 
                                                        child_order_acceptance_id=self._accepted_id)
                if len(results) <= 0:
                    print("bot: No order with id {}.".format(self._accepted_id))
                    self._post_process()
                    return
                self._accepted_jpy = results[0]["price"]
                if self.__DEBUG:
                    print(results[0])
                pass
            if self._tick_count >= self._tick_count_max:
                if self.__DEBUG:
                    print("bot: judge")
                else:
                    if self._side == "WAIT":
                        self.judge_order()
                    else:
                        self.judge_stop()
            self._post_process()
            if self.__DEBUG:
                print("bot: tick_count:", self._tick_count)
                print("bot: size of ltp list pnl list:", len(self._ltp_list), len(self._pnl_list))
        except Exception as ex:
            print(ex)
        
    def _calc_statistics(self, lst):
        """_calc_statistics(self) -> float, float, float, float
        calculate max., min., mean and std of values in a given list.

        Parameters
        ----------
        lst : list of values

        Returns
        -------
        max : float
        min : float
        mean : float
        std : float
        """
        ary = np.array(lst)
        return ary.max(), ary.min(), ary.mean(), ary.std()
    
    def judge_order(self):
        """judge_order(self) -> None
        judge whether a child order should be sent.
        """
        if self._side != "WAIT": # In normal use this syntax always returns False.
            return
        _, _2, ltp_mean, _3 = self._calc_statistics(self._ltp_list[-self._tick_count_max:])
        if ltp_mean <= self._ltp_list[0] - self._threshold:
            self._tmp_side = "SELL"
        elif ltp_mean > self._ltp_list[0] + self._threshold:
            self._tmp_side = "BUY"
        else:
            if self.__DEBUG:
                print("not satisfied with order condition.")
            return
        if self.__DEBUG:
            print("side:", self._tmp_side)
            return
        self.send_order()
        self._initialize_by_order()

    def send_order(self):
        """send_order(self) -> None
        send a child order according to the order setting.
        """
        # Order setting
        ## Child
        params = {
            "product_code":self._product_code,
            "child_order_type":self._order_condition,
            "side":self._tmp_side,
            "size":self.btc_size,
            "minute_to_expire":self._minute_to_expire
        }

        try:
            result = self._api.sendchildorder(**params)
            print(result)
            self._execution_list.append(result)
        except Exception as ex:
            print("@ sending order:", ex)
            self._tmp_side = self._side
    
    def _initialize_by_order(self):
        self._tick_count = 0
        self._side = self._tmp_side

    def judge_stop(self):
        """judge_stop(self)
        judge whether a stop order should be sent.
        """
        if self._side == "WAIT": # In normal use this syntax always returns False.
            return
        _, _2, pnl_mean, _3 = self._calc_statistics(self._pnl_list[-self._tick_count_max:])
        if self._pnl_list[-1] > self._cutting_ratio * self._profit_taking:
            if self._side == "BUY":
                self._tmp_side = "SELL"
            elif self._side == "SELL":
                self._tmp_side = "BUY"
            self.send_order()
            self._initialize_by_stop()
            return
        if pnl_mean > - self._loss_cutting and pnl_mean < self._profit_taking:
            if self.__DEBUG:
                print("not satisfied with order ")
            return
        if self.__DEBUG:
            if self._side == "BUY":
                self._tmp_side = "SELL"
            elif self._side == "SELL":
                self._tmp_side = "BUY"
            print("signal")
            self._initialize_by_stop()
            return
        
        if self._side == "BUY":
            self._tmp_side = "SELL"
        elif self._side == "SELL":
            self._tmp_side = "BUY"
        self.send_order()
        self._initialize_by_stop()
    
    def _initialize_by_stop(self):
        # self._pnl_list = []
        self._tick_count = 0
        self._side = "WAIT"
        self._tmp_side = "WAIT"
    
    def _post_process(self):
        if len(self._ltp_list) > 100:
            self._ltp_list.pop(0)
            self._pnl_list.pop(0)

def main():
    pass

if __name__ == "__main__":
    main()
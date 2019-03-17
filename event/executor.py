from __future__ import print_function

import json
import logging
from abc import ABCMeta, abstractmethod
import http.client as httplib

import oandapyV20
from oandapyV20.contrib.requests import MarketOrderRequest
import oandapyV20.endpoints.orders as orders

from broker.oanda.common.convertor import get_symbol


class ExecutionHandler(object):
    """
    Provides an abstract base class to handle all execution in the
    backtesting and live trading system.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self, event):
        """
        Send the order to the brokerage.
        """
        raise NotImplementedError("Should implement execute_order()")


class SimulatedExecution(object):
    """
    Provides a simulated execution handling environment. This class
    actually does nothing - it simply receives an order to execute.

    Instead, the Portfolio object actually provides fill handling.
    This will be modified in later versions.
    """

    def execute_order(self, event):
        pass


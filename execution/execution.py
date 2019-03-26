from __future__ import print_function

import http.client as httplib
import json
import logging
from abc import ABCMeta, abstractmethod

import oandapyV20
import oandapyV20.endpoints.orders as orders
from oandapyV20.contrib.requests import MarketOrderRequest

from broker.oanda.common.convertor import get_symbol
from event.event import SignalEvent, SignalAction
from event.handler import BaseHandler

logger = logging.getLogger(__name__)


class BaseExecutionHandler(BaseHandler):
    """
    Provides an abstract base class to handle all execution in the
    backtesting and live trading system.
    """
    subscription = [SignalEvent.type]

    __metaclass__ = ABCMeta

    def __init__(self, queue, account, *args, **kwargs):
        super(BaseExecutionHandler, self).__init__(queue)
        self.account = account

    @abstractmethod
    def open(self, event):
        raise NotImplementedError

    @abstractmethod
    def close(self, event):
        raise NotImplementedError

    @abstractmethod
    def update(self, event):
        raise NotImplementedError

    def process(self, event):
        if event.action == SignalAction.OPEN:
            self.open(event)
        if event.action == SignalAction.CLOSE:
            self.close(event)
        if event.action == SignalAction.UPDATE:
            self.update(event)


class SimulatedExecution(object):
    """
    Provides a simulated execution handling environment. This class
    actually does nothing - it simply receives an order to execute.

    Instead, the Portfolio object actually provides fill handling.
    This will be modified in later versions.
    """

    def execute_order(self, event):
        pass


class FXCMExecutionHandler(BaseExecutionHandler):

    def open(self, event):
        # check spread
        lots = self.account.get_lots(event.instrument)
        self.account.market_order(event.instrument,
                                  event.side,
                                  lots,
                                  take_profit=event.take_profit,
                                  stop_loss=event.stop_loss,
                                  trailing_pip=event.trailing_stop)
        event_dict = event.__dict__.copy()
        event_dict.pop('time')
        logger.info('[TRADE_OPEN] event = %s' % event_dict)

    def close(self, event):
        closed_trade = self.account.close_symbol(event.instrument, event.side, event.percent)
        for trade in closed_trade:
            pass
            # todo pop OrderClosedEvent
        logger.info('[ORDER_CLOSED] event = %s' % event.__dict__)

    def update(self, event):
        if event.trade_id:
            trailing_stop = event.trailing_stop
            # todo update trade
            self.account.update_trade(event.trade_id, is_stop=True, rate=event.stop_loss, is_in_pips=True)
            self.account.update_trade(event.trade_id, is_stop=False, rate=event.take_profit, is_in_pips=True)

        logger.info('[ORDER_UPDATE] event = %s' % event.__dict__)


class OANDAExecutionHandler(BaseExecutionHandler):
    def __init__(self, queue, account, domain, access_token, account_id):
        super(OANDAExecutionHandler, self).__init__(queue, account)
        self.domain = domain
        self.access_token = access_token
        self.account_id = account_id
        self.conn = self.obtain_connection()

    def obtain_connection(self):
        return httplib.HTTPSConnection(self.domain)

    def open(self, event):
        instrument = get_symbol(event.instrument)
        if event.order_type == 'market':
            if event.side == 'buy':
                mktOrder = MarketOrderRequest(
                    instrument=instrument,
                    units=event.units,
                    # type= event.order_type,
                    # side= event.side
                )
            if event.side == 'sell':
                mktOrder = MarketOrderRequest(
                    instrument=instrument,
                    units=(event.units * -1),
                    # type= event.order_type,
                    # side= event.side
                )
        else:
            print('Order Type Not Supported ' + self.order_type)
            return

        accountID = self.account_id
        access_token = self.access_token

        api = oandapyV20.API(access_token=access_token)

        r = orders.OrderCreate(accountID, data=mktOrder.data)
        try:
            # Try and execute order
            rv = api.request(r)
        except oandapyV20.exceptions.V20Error as err:
            print(r.status_code, err)
        else:
            print(json.dumps(rv, indent=2))

        # response = self.conn.getresponse().read().decode("utf-8").replace("\n","").replace("\t","")
        logger.debug(json.dumps(rv, indent=2))

from __future__ import print_function

import http.client as httplib
import json
import logging
from abc import ABCMeta, abstractmethod

import oandapyV20
import oandapyV20.endpoints.orders as orders
from oandapyV20.contrib.requests import MarketOrderRequest

from broker.fxcm.constants import get_fxcm_symbol
from broker.oanda.common.convertor import get_symbol
from event.event import SignalEvent, SignalAction, TradeOpenEvent
from event.handler import BaseHandler
from mt4.constants import OrderSide
from utils.time import str_to_datetime

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
        # check order exist
        if self.check_trade_exist(event.instrument, event.side):
            logger.info('[ORDER_OPEN_SKIP] %s' % event.__dict__)
            return

        # check spread
        lots = self.account.get_lots(event.instrument)
        success, trade = self.account.market_order(event.instrument,
                                                   event.side,
                                                   lots,
                                                   take_profit=event.take_profit,
                                                   stop_loss=event.stop_loss,
                                                   trailing_pip=event.trailing_stop)
        event_dict = event.__dict__.copy()
        event_dict.pop('time')
        if success:
            logger.info('[TRADE_OPEN] event = %s' % event_dict)
            open_time = trade.get_time()
            open_price = trade.get_buy() if trade.get_isBuy() else trade.get_sell()

            event = TradeOpenEvent(broker=self.account.broker, account_id=self.account.account_id,
                                   trade_id=int(trade.get_tradeId()), lots=event.lots,
                                   instrument=event.instrument, side=event.side, open_time=open_time,
                                   open_price=open_price,
                                   stop_loss=trade.get_stopRate(),
                                   take_profit=trade.get_limitRate(),
                                   magic_number=event.magic_number)
            self.put(event)
        else:
            logger.info('[TRADE_OPEN] event = %s' % event_dict)
            logger.error('[TRADE_OPEN_FAILED] error = %s' % trade)

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

    def check_trade_exist(self, instrument, side):
        instrument = get_fxcm_symbol(instrument)
        is_buy = side == OrderSide.BUY
        for id, trade in self.account.get_trades():
            trade_instrument = get_fxcm_symbol(trade.get_currency())
            if trade_instrument == instrument and is_buy == trade.get_isBuy():
                return True
        return False


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

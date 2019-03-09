import logging

from broker.base import TradeBase
from mt4.constants import OrderSide

from broker.oanda.base import api, OANDABase
from broker.oanda.common.logger import log_error
from broker.oanda.common.prints import print_trades
from broker.oanda.common.view import print_entity, print_response_entity
from broker.oanda.common.convertor import get_symbol, lots_to_units
from broker.oanda.common.constants import TransactionName, OrderType, OrderPositionFill, TimeInForce, \
    OrderTriggerCondition
import settings

logger = logging.getLogger(__name__)


class TradeMixin(OANDABase, TradeBase):


    def list_trade(self, ids=None, state=None, instrument=None, count=20, beforeID=None):
        return self.fxcmpy.get_all_trade_ids()


    def list_open_trade(self):
        return self.fxcmpy.get_open_trade_ids()

    def get_closed_trade_ids(self):
        return self.fxcmpy.get_closed_trade_ids()


    def get_trade(self, trade_id):
        return self.fxcmpy.get_order(trade_id)


    def close(self, trade_id, lots):
        return self.fxcmpy.close_trade( trade_id, lots, order_type='AtMarket',
                    time_in_force='IOC', rate=None, at_market=None)


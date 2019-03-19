import logging

from broker.base import TradeBase
from broker.oanda.base import OANDABase
from broker.oanda.common.convertor import lots_to_units

logger = logging.getLogger(__name__)


class TradeMixin(OANDABase, TradeBase):

    def list_trade(self, ids=None, state=None, instrument=None, count=20, beforeID=None):
        return self.fxcmpy.get_all_trade_ids()

    def list_open_trade(self):
        return self.fxcmpy.get_open_trade_ids()

    def open_trade_ids(self):
        return self.fxcmpy.get_open_trade_ids()

    def get_closed_trade_ids(self):
        return self.fxcmpy.get_closed_trade_ids()

    def get_trade(self, trade_id):
        return self.fxcmpy.open_pos.get(trade_id)

    def close_trade(self, trade_id, lots=None, percent=None):
        amount = self.get_trade(trade_id).get_amount()
        if percent:
            amount = amount * percent
        elif lots:
            amount = lots_to_units(lots)

        try:
            self.fxcmpy.close_trade(trade_id, amount, order_type='AtMarket',
                                    time_in_force='IOC', rate=None, at_market=None)
        except Exception as ex:
            logger.error('[Closet Trade] %s' % ex)

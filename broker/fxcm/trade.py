import logging

from broker.base import TradeBase
from broker.fxcm.constants import get_fxcm_symbol
from broker.oanda.base import OANDABase
from broker.oanda.common.convertor import lots_to_units
from mt4.constants import OrderSide

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
            amount = lots_to_units(lots) / 1000

        try:
            self.fxcmpy.close_trade(trade_id, amount, order_type='AtMarket',
                                    time_in_force='IOC', rate=None, at_market=None)
        except Exception as ex:
            logger.error('[Closet Trade] %s' % ex)

    def close_symbol(self, instrument, side, percent=None):
        instrument = get_fxcm_symbol(instrument)
        data = []
        for trade_id, trade in self.fxcmpy.open_pos.items():

            if instrument == trade.get_currency():
                trade_side = OrderSide.BUY if trade.get_isBuy() else OrderSide.SELL
                if trade_side == side:
                    units = trade.get_amount()

                    if percent and 1 >= percent > 0:
                        units = int(units * percent)

                    try:
                        trade.close(amount=units)
                        data.append({'trade_id': trade_id, 'side': side, 'instrument': instrument, 'units': units})
                    except Exception as ex:
                        logger.error('Cant close trade = %s, %s' % (trade_id, ex))
        return data

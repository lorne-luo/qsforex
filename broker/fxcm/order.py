import logging

import settings
from broker.base import OrderBase
from broker.fxcm.constants import get_fxcm_symbol
from broker.oanda.common.constants import TimeInForce, OrderPositionFill, OrderTriggerCondition
from broker.oanda.common.convertor import lots_to_units
from mt4.constants import OrderSide
from utils.string import format_dict

logger = logging.getLogger(__name__)


class OrderMixin(OrderBase):

    def list_order(self, ids=None, state=None, instrument=None, count=100, beforeID=None):
        return self.fxcmpy.get_orders('list')

    def list_pending_order(self):
        orders = self.list_order()
        if orders.bool():
            return orders[orders['status'] in ['1', '7']].T.to_dict()
        return []

    def open_order_ids(self):
        return [int(x.get('orderId')) for x in self.fxcmpy.get_orders('list')]

    def get_order(self, order_id):
        order_id = int(order_id)
        return self.fxcmpy.get_order(order_id)

    def create_entry_order(self, symbol, is_buy, amount, time_in_force=TimeInForce.GTC, take_profit=0,
                           price=0, stop_loss=None, trailing_step=None,
                           trailing_pip=None, order_range=None,
                           expiration=None, **kwargs):
        is_in_pips = kwargs.get('is_in_pips', True)

        if is_in_pips and stop_loss and stop_loss > 0:
            stop_loss = -1 * stop_loss # change to negtive if using pips

        return self.fxcmpy.create_entry_order(symbol, is_buy, amount,
                                              is_in_pips=is_in_pips,
                                              time_in_force=time_in_force, rate=price,
                                              stop=stop_loss,
                                              limit=take_profit,
                                              trailing_stop_step=trailing_pip,
                                              trailing_step=trailing_step)

    def _make_limit_or_stop_order(self, instrument, side, price, lots, take_profit=None, stop_loss=None,
                                  trailing_pip=None, **kwargs):
        symbol = get_fxcm_symbol(instrument)
        is_buy = side == OrderSide.BUY
        amount = lots_to_units(lots) / 1000
        is_in_pips = kwargs.get('is_in_pips', True)

        order_id = kwargs.get('order_id', None)
        if order_id:
            order = self.get_order(order_id)
            if trailing_pip:
                order.set_trailing_step(trailing_pip)

            kw = {}
            if stop_loss:
                kw['stop'] = stop_loss
                kw['is_stop_in_pips'] = is_in_pips
            if take_profit:
                kw['limit'] = take_profit
                kw['is_limit_in_pips'] = is_in_pips
            if kw:
                self.fxcmpy.change_order_stop_limit(order_id, **kw)
        else:
            return self.create_entry_order(symbol, is_buy, amount,
                                           time_in_force=TimeInForce.GTC, price=price,
                                           take_profit=take_profit,
                                           stop_loss=stop_loss, trailing_pip=trailing_pip,
                                           **kwargs)

    def limit_order(self, instrument, side, price, lots, take_profit=None, stop_loss=None, trailing_pip=None,
                    **kwargs):

        return self._make_limit_or_stop_order(instrument, side, price,
                                              take_profit,
                                              stop_loss,
                                              trailing_pip,
                                              **kwargs)

    def stop_order(self, instrument, side, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):

        return self._make_limit_or_stop_order(instrument, side, price, lots, take_profit, stop_loss, trailing_pip,
                                              **kwargs)

    def update_order(self, order_id,
                     take_profit=None,
                     stop_loss=None,
                     is_in_pips=True):
        if not order_id:
            return
        order_id = int(order_id)

        kw = {}
        if stop_loss:
            kw['stop'] = stop_loss
            kw['is_stop_in_pips'] = is_in_pips
        if take_profit:
            kw['limit'] = take_profit
            kw['is_limit_in_pips'] = is_in_pips
        if kw:
            self.fxcmpy.change_order_stop_limit(order_id, **kw)

    def market_order(self, instrument, side, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        timeInForce = kwargs.get('timeInForce', TimeInForce.FOK)
        symbol = get_fxcm_symbol(instrument)
        is_buy = side == OrderSide.BUY
        amount = lots_to_units(lots) / 1000
        is_in_pips = kwargs.get('is_in_pips', True)

        if is_in_pips and stop_loss and stop_loss > 0:
            stop_loss = -1 * stop_loss  # change to negtive if using pips

        return self.fxcmpy.open_trade(symbol, is_buy,
                                      amount, timeInForce, order_type='AtMarket', rate=0,
                                      is_in_pips=is_in_pips, limit=take_profit, at_market=0, stop=stop_loss,
                                      trailing_step=trailing_pip, account_id=self.account_id)

    # ================================================================================= TP , SL and trailing SL

    def take_profit(self, trade_id, price, **kwargs):
        """
        1. self.take_profit(order_id, 40, is_in_pips=True)
        2. self.take_profit(order_id, 1.1324)
        """
        trade_id = int(trade_id)
        is_in_pips = kwargs.get('is_in_pips', True)

        if trade_id in self.open_order_ids():
            self.fxcmpy.change_order_stop_limit(trade_id, limit=price, is_limit_in_pips=is_in_pips)
        elif trade_id in self.open_trade_ids():
            self.fxcmpy.change_trade_stop_limit(trade_id, False, price, is_in_pips=is_in_pips)

    def stop_loss(self, trade_id, price, **kwargs):
        """
        1. self.stop_loss(order_id, -40, is_in_pips=True)
        2. self.stop_loss(order_id, 1.1324)
        """
        trade_id = int(trade_id)
        is_in_pips = kwargs.get('is_in_pips', True)
        if is_in_pips and price > 0:
            price = -1 * price # change to negtive if using pips

        if trade_id in self.open_order_ids():
            self.fxcmpy.change_order_stop_limit(trade_id, stop=price, is_stop_in_pips=is_in_pips)
        elif trade_id in self.open_trade_ids():
            self.fxcmpy.change_trade_stop_limit(trade_id, True, price, is_in_pips=is_in_pips)

    def trailing_stop_loss(self, trade_id, pips, **kwargs):
        trade_id = int(trade_id)
        is_in_pips = kwargs.get('is_in_pips', True)

        # @fixme
        if trade_id in self.open_order_ids():
            pass
        elif trade_id in self.open_trade_ids():
            self.fxcmpy.change_trade_stop_limit(trade_id, is_in_pips=is_in_pips, trailing_step=pips)

    # cancel & extensions
    def cancel_order(self, order_id, **kwargs):
        order_id = int(order_id)
        self.fxcmpy.delete_order(order_id)
        return True

    def log_order(self):
        logger.info('[LOG_ORDER]')
        orders = self.fxcmpy.get_orders('list')
        for order in orders:
            content = format_dict(order)
            logger.info(content)

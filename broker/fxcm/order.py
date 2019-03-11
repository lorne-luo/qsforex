import logging

from broker.base import OrderBase
from broker.fxcm.constants import get_fxcm_symbol
from broker.oanda.common.constants import TimeInForce, OrderPositionFill, OrderTriggerCondition
from broker.oanda.common.convertor import lots_to_units
from mt4.constants import OrderSide, pip

logger = logging.getLogger(__name__)


class OrderMixin(OrderBase):

    def list_order(self, ids=None, state=None, instrument=None, count=100, beforeID=None):
        return self.fxcmpy.get_orders()

    def list_pending_order(self):
        orders = self.list_order()
        # todo check fxcmpy_order status list
        return orders[orders['status'] in ['1', '7']].T.to_dict()

    def get_order(self, order_id):
        return self.fxcmpy.get_order(order_id)

    def create_entry_order(self, symbol, is_buy, amount, time_in_force=TimeInForce.GTC, take_profit_price=0,
                           price=0, stop_loss_pip=None, trailing_step=None,
                           trailing_pip=None, order_range=None,
                           expiration=None):

        order = self.fxcmpy.create_entry_order(symbol, is_buy, amount,
                                               is_in_pips=True,
                                               time_in_force=time_in_force, rate=price,
                                               stop=stop_loss_pip, trailing_stop_step=trailing_pip,
                                               trailing_step=trailing_step)
        self.fxcmpy.change_order_stop_limit(order.get_orderId(), stop=None, limit=take_profit_price,
                                            is_stop_in_pips=None,
                                            is_limit_in_pips=False)

        return order

    def limit_order(self, instrument, side, price,
                    lots, timeInForce=TimeInForce.GTC,
                    positionFill=OrderPositionFill.DEFAULT,
                    trigger_condition=OrderTriggerCondition.DEFAULT,
                    gtd_time=None,
                    take_profit_price=None,
                    stop_loss_pip=None,
                    trailing_pip=None,
                    order_id=None,  # order to replace
                    client_id=None, client_tag=None, client_comment=None):
        symbol = get_fxcm_symbol(instrument)
        is_buy = side == OrderSide.BUY
        amount = lots_to_units(lots)

        try:
            if order_id:
                order = self.get_order(order_id)
                order.set_trailing_step(trailing_pip)  # todo
                order.set_stop_rate(stop_rate=stop_loss_pip, is_in_pips=True)
                self.fxcmpy.change_order_stop_limit(order_id, stop=None, limit=take_profit_price, is_stop_in_pips=None,
                                                    is_limit_in_pips=False)
            else:
                order = self.create_entry_order(symbol, is_buy, amount,
                                                time_in_force=TimeInForce.GTC, price=price,
                                                take_profit_price=take_profit_price,
                                                stop_loss_pip=stop_loss_pip, trailing_pip=trailing_pip)
        except Exception as ex:
            print(ex)
            return False
        return order

    def limit_buy(self, instrument, price,
                  lots=0.1, timeInForce=TimeInForce.GTC,
                  positionFill=OrderPositionFill.DEFAULT,
                  trigger_condition=OrderTriggerCondition.DEFAULT,
                  gtd_time=None,
                  take_profit_price=None,
                  stop_loss_pip=None,
                  trailing_pip=None,
                  order_id=None,  # order to replace
                  client_id=None, client_tag=None, client_comment=None):
        """buy shortcut for limit order"""
        return self.limit_order(instrument=instrument, side=OrderSide.BUY, price=price,
                                lots=lots, timeInForce=timeInForce,
                                positionFill=positionFill,
                                trigger_condition=trigger_condition,
                                gtd_time=gtd_time,
                                take_profit_price=take_profit_price,
                                stop_loss_pip=stop_loss_pip,
                                trailing_pip=trailing_pip,
                                order_id=order_id,
                                client_id=client_id, client_tag=client_tag, client_comment=client_comment)

    def limit_sell(self, instrument, price,
                   lots=0.1, timeInForce=TimeInForce.GTC,
                   positionFill=OrderPositionFill.DEFAULT,
                   trigger_condition=OrderTriggerCondition.DEFAULT,
                   gtd_time=None,
                   take_profit_price=None,
                   stop_loss_pip=None,
                   trailing_pip=None,
                   order_id=None,  # order to replace
                   client_id=None, client_tag=None, client_comment=None):
        """sell shortcut for limit order"""
        return self.limit_order(instrument=instrument, side=OrderSide.SELL, price=price,
                                lots=lots, timeInForce=timeInForce,
                                positionFill=positionFill,
                                trigger_condition=trigger_condition,
                                gtd_time=gtd_time,
                                take_profit_price=take_profit_price,
                                stop_loss_pip=stop_loss_pip,
                                trailing_pip=trailing_pip,
                                order_id=order_id,
                                client_id=client_id, client_tag=client_tag, client_comment=client_comment)

    def stop_order(self, instrument, side, price,
                   lots, timeInForce=TimeInForce.GTC,
                   positionFill=OrderPositionFill.DEFAULT, priceBound=None,
                   trigger_condition=OrderTriggerCondition.DEFAULT,
                   gtd_time=None,
                   take_profit_price=None,
                   stop_loss_pip=None,
                   trailing_pip=None,
                   order_id=None,  # order to replace
                   client_id=None, client_tag=None, client_comment=None):
        symbol = get_fxcm_symbol(instrument)
        is_buy = side == OrderSide.BUY
        amount = lots_to_units(lots)

        try:
            if order_id:
                order = self.get_order(order_id)
                order.set_trailing_step(trailing_pip)  # todo
                order.set_stop_rate(stop_rate=stop_loss_pip, is_in_pips=True)
                self.fxcmpy.change_order_stop_limit(order_id, stop=None, limit=take_profit_price, is_stop_in_pips=None,
                                                    is_limit_in_pips=False)
            else:
                order = self.create_entry_order(symbol, is_buy, amount,
                                                time_in_force=TimeInForce.GTC, price=price,
                                                take_profit_price=take_profit_price,
                                                stop_loss_pip=stop_loss_pip, trailing_pip=trailing_pip)
        except Exception as ex:
            print(ex)
            return False
        return order

    def stop_buy(self, instrument, price,
                 lots=0.1, timeInForce=TimeInForce.GTC,
                 positionFill=OrderPositionFill.DEFAULT, priceBound=None,
                 trigger_condition=OrderTriggerCondition.DEFAULT,
                 gtd_time=None,
                 take_profit_price=None,
                 stop_loss_pip=None,
                 trailing_pip=None,
                 order_id=None,  # order to replace
                 client_id=None, client_tag=None, client_comment=None):
        """buy shortcut for stop order"""
        return self.stop_order(instrument=instrument, side=OrderSide.BUY, price=price,
                               lots=lots, timeInForce=timeInForce, priceBound=priceBound,
                               positionFill=positionFill,
                               trigger_condition=trigger_condition,
                               gtd_time=gtd_time,
                               take_profit_price=take_profit_price,
                               stop_loss_pip=stop_loss_pip,
                               trailing_pip=trailing_pip,
                               order_id=order_id,
                               client_id=client_id, client_tag=client_tag, client_comment=client_comment)

    def stop_sell(self, instrument, price,
                  lots=0.1, timeInForce=TimeInForce.GTC,
                  positionFill=OrderPositionFill.DEFAULT, priceBound=None,
                  trigger_condition=OrderTriggerCondition.DEFAULT,
                  gtd_time=None,
                  take_profit_price=None,
                  stop_loss_pip=None,
                  trailing_pip=None,
                  order_id=None,  # order to replace
                  client_id=None, client_tag=None, client_comment=None):
        """sell shortcut for stop order"""
        return self.stop_order(instrument=instrument, side=OrderSide.SELL, price=price,
                               lots=lots, timeInForce=timeInForce, priceBound=priceBound,
                               positionFill=positionFill,
                               trigger_condition=trigger_condition,
                               gtd_time=gtd_time,
                               take_profit_price=take_profit_price,
                               stop_loss_pip=stop_loss_pip,
                               trailing_pip=trailing_pip,
                               order_id=order_id,
                               client_id=client_id, client_tag=client_tag, client_comment=client_comment)

    def market_order(self, instrument, side,
                     lots, timeInForce=TimeInForce.FOK,
                     priceBound=None, positionFill=OrderPositionFill.DEFAULT,
                     take_profit_price=None,
                     stop_loss_pip=None,
                     trailing_pip=None,
                     client_id=None, client_tag=None, client_comment=None,
                     trade_client_id=None, trade_client_tag=None, trade_client_comment=None):
        symbol = get_fxcm_symbol(instrument)
        is_buy = side == OrderSide.BUY
        amount = lots_to_units(lots)

        try:
            order = self.fxcmpy.open_trade(symbol, is_buy,
                                           amount, timeInForce, order_type='AtMarket', rate=0,
                                           is_in_pips=True, limit=None, at_market=0, stop=stop_loss_pip,
                                           trailing_step=trailing_pip, account_id=self.account_id)
            order.set_stop_rate(take_profit_price, is_in_pips=False)
        except Exception as ex:
            print(ex)
            return False
        return True

    # TP , SL and trailing SL

    def take_profit(self, trade_id, price, order_id=None, client_trade_id=None,
                    timeInForce=TimeInForce.GTC, gtd_time=None,
                    trigger_condition=OrderTriggerCondition.DEFAULT,
                    client_id=None, client_tag=None, client_comment=None):
        self.fxcmpy.change_order_stop_limit(trade_id, limit=price, is_limit_in_pips=False)

    def stop_loss(self, trade_id, stop_loss_pip=None, price=None, order_id=None, client_trade_id=None,
                  timeInForce=TimeInForce.GTC, gtd_time=None,
                  trigger_condition=OrderTriggerCondition.DEFAULT,
                  guaranteed=None,
                  client_id=None, client_tag=None, client_comment=None):
        self.fxcmpy.change_order_stop_limit(trade_id, stop=price, is_stop_in_pips=False)

    def trailing_stop_loss(self, trade_id, stop_loss_pip=None, order_id=None, client_trade_id=None,
                           timeInForce=TimeInForce.GTC, gtd_time=None,
                           trigger_condition=OrderTriggerCondition.DEFAULT,
                           client_id=None, client_tag=None, client_comment=None):

        pass

    # cancel & extensions
    def cancel_order(self, order_id):
        self.fxcmpy.delete_order(order_id)
        return True

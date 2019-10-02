import logging
from decimal import Decimal

from v20.transaction import StopLossDetails, ClientExtensions, TakeProfitDetails, TrailingStopLossDetails, \
    LimitOrderTransaction, StopOrderTransaction

import settings
from broker.base import OrderBase
from broker.oanda.base import api, OANDABase
from broker.oanda.common.constants import TransactionName, OrderType, OrderPositionFill, TimeInForce, \
    OrderTriggerCondition, OrderState
from broker.oanda.common.convertor import get_symbol, lots_to_units
from broker.oanda.common.logger import log_error
from broker.oanda.common.prints import print_orders
from broker.oanda.common.view import print_entity
from mt4.constants import OrderSide, pip

logger = logging.getLogger(__name__)


class OrderMixin(OANDABase, OrderBase):

    # order list
    def _process_orders(self, response):
        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'LIST_ORDER')
            return []

        orders = response.get("orders", "200")
        if len(orders) == 0:
            logger.debug("Account {} has no pending Orders to cancel".format(
                self.account_id
            ))
        for order in orders:
            self.orders[order.id] = order

        if settings.DEBUG:
            print_orders(orders)
        return orders

    def list_order(self, ids=None, state=None, instrument=None, count=20, beforeID=None):
        data = {}
        if ids:
            data['ids'] = str(ids)
        if state:
            data['state'] = state
        if instrument:
            data['instrument'] = instrument
        if count:
            data['count'] = str(count)
        if beforeID:
            data['beforeID'] = str(beforeID)
        response = api.order.list(self.account_id, **data)
        return self._process_orders(response)

    def list_pending_order(self):
        response = api.order.list_pending(self.account_id)
        return self._process_orders(response)

    # order creation
    def _process_order_paramters(self, **kwargs):
        data = {}
        instrument = None
        pip_unit = None

        if kwargs.get('instrument'):
            instrument = get_symbol(kwargs['instrument'])

            data['instrument'] = instrument

        if kwargs.get('trade_id'):
            data['tradeID'] = str(kwargs['trade_id'])
            trade = self.trades.get(data['tradeID']) or self.get_trade(data['tradeID'])
            instrument = trade.instrument

        if instrument:
            pip_unit = pip(instrument)

        if kwargs.get('lots'):
            units = lots_to_units(kwargs['lots'], kwargs.get('side') or OrderSide.BUY)
            data['units'] = str(units)

        if kwargs.get('type'):
            data['type'] = kwargs['type']

        if kwargs.get('timeInForce'):
            data['timeInForce'] = kwargs['timeInForce'] or TimeInForce.FOK

        if kwargs.get('priceBound'):
            data['priceBound'] = str(kwargs['priceBound'])

        if kwargs.get('price'):
            data['price'] = str(kwargs['price'])

        if kwargs.get('positionFill'):
            data['positionFill'] = kwargs['positionFill'] or OrderPositionFill.DEFAULT

        # The Client Extensions to update for the Order. Do not set, modify, or
        # delete clientExtensions if your account is associated with MT4.
        if kwargs.get('client_id') or kwargs.get('client_tag') or kwargs.get('client_comment'):
            data['clientExtensions'] = ClientExtensions(id=kwargs['client_id'],
                                                        tag=kwargs['client_tag'],
                                                        comment=kwargs['client_comment'])

        if kwargs.get('trade_client_id') or kwargs.get('trade_client_tag') or kwargs.get('trade_client_comment'):
            data['tradeClientExtensions'] = ClientExtensions(id=kwargs['trade_client_id'],
                                                             tag=kwargs['trade_client_tag'],
                                                             comment=kwargs['trade_client_comment'])

        if kwargs.get('take_profit_price'):
            data['takeProfitOnFill'] = TakeProfitDetails(
                price=str(kwargs['take_profit_price']),
                clientExtensions=data.get('clientExtensions')
            )

        if kwargs.get('stop_loss_pip') and pip_unit:
            stop_loss_price = pip_unit * Decimal(str(kwargs['stop_loss_pip']))
            data['stopLossOnFill'] = StopLossDetails(distance=str(stop_loss_price),
                                                     clientExtensions=data.get('clientExtensions'))

        if kwargs.get('stop_loss_distance'):
            data['stopLossOnFill'] = StopLossDetails(distance=str(kwargs['stop_loss_distance']),
                                                     clientExtensions=data.get('clientExtensions'))

        if kwargs.get('trailing_pip'):
            trailing_distance_price = pip_unit * Decimal(str(kwargs['trailing_pip']))
            data['trailingStopLossOnFill'] = TrailingStopLossDetails(distance=str(trailing_distance_price),
                                                                     clientExtensions=data.get('clientExtensions'))

        if kwargs.get('trigger_condition'):
            data['triggerCondition'] = kwargs['trigger_condition'] or OrderTriggerCondition.DEFAULT

        if kwargs.get('gtd_time'):
            # todo confirm gtdTime format
            data['gtdTime'] = str(kwargs['gtd_time'])

        if kwargs.get('client_trade_id'):
            data['clientTradeID'] = kwargs['client_trade_id']

        if kwargs.get('guaranteed'):
            data['guaranteed'] = kwargs['guaranteed']

        if kwargs.get('distance'):
            data['distance'] = kwargs['distance']

        return data

    def _process_order_response(self, response, func_name, response_status="200"):
        if response.status < 200 or response.status > 299:
            log_error(logger, response, func_name)
            raise Exception(response.body.get('errorMessage'))

        transactions = []
        trade_ids = []
        order_ids = []
        for name in TransactionName.all():
            try:
                transaction = response.get(name, response_status)
                transactions.append(transaction)

                to = getattr(transaction, 'tradeOpened', None)
                if to:
                    trade_ids.append(to.tradeID)

                if isinstance(transaction, LimitOrderTransaction) or isinstance(transaction, StopOrderTransaction):
                    order_ids.append(transaction.id)
            except:
                pass

        if trade_ids or order_ids:
            self.pull()

        if settings.DEBUG:
            for t in transactions:
                print_entity(t, title=t.__class__.__name__)
                print('')
        return transactions

    def get_order(self, order_id):
        response = api.order.get(self.account_id, str(order_id))
        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'GET_ORDER')
            return None

        order = response.get("order", "200")
        self.orders[order.id] = order

        if settings.DEBUG:
            print_orders([order])
        return order

    def limit_order(self, instrument, side, price,
                    lots=0.1, timeInForce=TimeInForce.GTC,
                    positionFill=OrderPositionFill.DEFAULT,
                    trigger_condition=OrderTriggerCondition.DEFAULT,
                    gtd_time=None,
                    take_profit=None,
                    stop_loss=None,
                    trailing_pip=None,
                    order_id=None,  # order to replace
                    client_id=None, client_tag=None, client_comment=None,
                    **kwargs):
        data = {'instrument': instrument, 'side': side, 'lots': lots, 'type': OrderType.LIMIT,
                'timeInForce': timeInForce,
                'price': price, 'positionFill': positionFill, 'take_profit_price': take_profit,
                'trigger_condition': trigger_condition, 'gtd_time': gtd_time,
                'stop_loss_pip': stop_loss, 'trailing_pip': trailing_pip, 'client_id': client_id,
                'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)

        if order_id:
            response = self.api.order.limit_replace(self.account_id, str(order_id), **kwargs)
        else:
            response = self.api.order.limit(self.account_id, **kwargs)

        return self._process_order_response(response, 'LIMIT_ORDER', "201")

    def stop_order(self, instrument, side, price,
                   lots=0.1, timeInForce=TimeInForce.GTC,
                   positionFill=OrderPositionFill.DEFAULT, priceBound=None,
                   trigger_condition=OrderTriggerCondition.DEFAULT,
                   gtd_time=None,
                   take_profit=None,
                   stop_loss=None,
                   trailing_pip=None,
                   order_id=None,  # order to replace
                   client_id=None, client_tag=None, client_comment=None,
                   **kwargs):
        data = {'instrument': instrument, 'side': side, 'lots': lots, 'type': OrderType.STOP,
                'timeInForce': timeInForce,
                'price': price, 'positionFill': positionFill, 'take_profit_price': take_profit,
                'trigger_condition': trigger_condition, 'gtd_time': gtd_time, 'priceBound': priceBound,
                'stop_loss_pip': stop_loss, 'trailing_pip': trailing_pip, 'client_id': client_id,
                'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)

        if order_id:
            response = self.api.order.stop_replace(self.account_id, str(order_id), **kwargs)
        else:
            response = self.api.order.stop(self.account_id, **kwargs)

        return self._process_order_response(response, 'STOP_ORDER', "201")

    def market_order(self, instrument, side,
                     lots=0.1, timeInForce=TimeInForce.FOK,
                     priceBound=None, positionFill=OrderPositionFill.DEFAULT,
                     take_profit=None,
                     stop_loss=None,
                     trailing_pip=None,
                     client_id=None, client_tag=None, client_comment=None,
                     trade_client_id=None, trade_client_tag=None, trade_client_comment=None,
                     **kwargs):

        data = {'instrument': instrument, 'side': side, 'lots': lots, 'type': OrderType.MARKET,
                'timeInForce': timeInForce,
                'priceBound': priceBound, 'positionFill': positionFill, 'take_profit_price': take_profit,
                'stop_loss_pip': stop_loss, 'trailing_pip': trailing_pip, 'client_id': client_id,
                'client_tag': client_tag, 'client_comment': client_comment, 'trade_client_id': trade_client_id,
                'trade_client_tag': trade_client_tag, 'trade_client_comment': trade_client_comment}
        kwargs = self._process_order_paramters(**data)

        response = self.api.order.market(self.account_id, **kwargs)

        return self._process_order_response(response, 'MARKET_ORDER', "201")

        # todo fail: ORDER_CANCEL,MARKET_ORDER_REJECT
        # todo success:MARKET_ORDER + ORDER_FILL

    def market_if_touched(self, instrument, side, price, lots=0.1,
                          priceBound=None, timeInForce=TimeInForce.GTC,
                          gtd_time=None, positionFill=OrderPositionFill.DEFAULT,
                          trigger_condition=OrderTriggerCondition.DEFAULT,
                          take_profit=None,
                          stop_loss=None,
                          trailing_pip=None,
                          order_id=None,  # order to replace
                          client_id=None, client_tag=None, client_comment=None,
                          trade_client_id=None, trade_client_tag=None, trade_client_comment=None,
                          **kwargs):
        data = {'instrument': instrument, 'side': side, 'lots': lots, 'type': OrderType.MARKET_IF_TOUCHED,
                'timeInForce': timeInForce, 'gtd_time': gtd_time, 'trigger_condition': trigger_condition,
                'priceBound': priceBound, 'positionFill': positionFill, 'take_profit_price': take_profit,
                'stop_loss_pip': stop_loss, 'trailing_pip': trailing_pip, 'client_id': client_id,
                'client_tag': client_tag, 'client_comment': client_comment, 'trade_client_id': trade_client_id,
                'trade_client_tag': trade_client_tag, 'trade_client_comment': trade_client_comment, 'price': price}
        kwargs = self._process_order_paramters(**data)

        if order_id:
            response = self.api.order.market_if_touched_replace(self.account_id, str(order_id), **kwargs)
        else:
            response = self.api.order.market_if_touched(self.account_id, **kwargs)

        transactions = self._process_order_response(response, 'MARKET_IF_TOUCHED', "201")

        return transactions

    # TP , SL and trailing SL

    def take_profit(self, trade_id, price, order_id=None, client_trade_id=None,
                    timeInForce=TimeInForce.GTC, gtd_time=None,
                    trigger_condition=OrderTriggerCondition.DEFAULT,
                    client_id=None, client_tag=None, client_comment=None,
                    **kwargs):
        data = {'price': price, 'client_trade_id': client_trade_id, 'trade_id': trade_id,
                'type': OrderType.TAKE_PROFIT, 'timeInForce': timeInForce,
                'trigger_condition': trigger_condition, 'gtd_time': gtd_time,
                'client_id': client_id, 'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)

        if order_id:
            response = self.api.order.take_profit_replace(self.account_id, str(order_id), **kwargs)
        else:
            response = self.api.order.take_profit(self.account_id, **kwargs)

        transactions = self._process_order_response(response, 'TAKE_PROFIT', "201")

        return transactions

    def stop_loss(self, trade_id, stop_loss_pip=None, price=None, order_id=None, client_trade_id=None,
                  timeInForce=TimeInForce.GTC, gtd_time=None,
                  trigger_condition=OrderTriggerCondition.DEFAULT,
                  guaranteed=None,
                  client_id=None, client_tag=None, client_comment=None,
                  **kwargs):
        data = {'client_trade_id': client_trade_id, 'trade_id': trade_id,
                'price': price, 'stop_loss_pip': stop_loss_pip,
                'type': OrderType.STOP_LOSS, 'timeInForce': timeInForce, 'guaranteed': guaranteed,
                'trigger_condition': trigger_condition, 'gtd_time': gtd_time,
                'client_id': client_id, 'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)

        if order_id:
            response = self.api.order.stop_loss_replace(self.account_id, str(order_id), **kwargs)
        else:
            response = self.api.order.stop_loss(self.account_id, **kwargs)

        transactions = self._process_order_response(response, 'STOP_LOSS', "201")

        return transactions

    def trailing_stop_loss(self, trade_id, stop_loss_pip=None, order_id=None, client_trade_id=None,
                           timeInForce=TimeInForce.GTC, gtd_time=None,
                           trigger_condition=OrderTriggerCondition.DEFAULT,
                           client_id=None, client_tag=None, client_comment=None,
                           **kwargs):
        data = {'trade_id': trade_id, 'client_trade_id': client_trade_id,
                'stop_loss_pip': stop_loss_pip,
                'type': OrderType.TRAILING_STOP_LOSS, 'timeInForce': timeInForce,
                'trigger_condition': trigger_condition, 'gtd_time': gtd_time,
                'client_id': client_id, 'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)

        if order_id:
            response = self.api.order.trailing_stop_loss_replace(self.account_id, str(order_id), **kwargs)
        else:
            response = self.api.order.trailing_stop_loss(self.account_id, **kwargs)

        transactions = self._process_order_response(response, 'TRAILING_STOP_LOSS', "201")

        return transactions

    # cancel & extensions
    def cancel_order(self, order_id, **kwargs):
        response = api.order.cancel(self.account_id, str(order_id))

        # print("Response: {} ({})".format(response.status, response.reason))

        if response.status < 200 or response.status > 299:
            transaction = response.get('orderCancelRejectTransaction', "404")
            if settings.DEBUG:
                print_entity(transaction, title='Order Cancel Reject')
            raise Exception('orderCancelRejectTransaction')

        transaction = response.get('orderCancelTransaction', "200")
        if settings.DEBUG:
            print_entity(transaction, title='Order Canceled')

        order_id = transaction.orderID
        if order_id in self.orders:
            self.orders.pop(order_id)

        return transaction

    def cancel_pending_order(self):
        """cancel all pending orders"""
        if not self.orders:
            self.list_order()

        ids = self.orders.keys()

        for id in ids:
            order = self.orders.get(id)
            if order.state == OrderState.PENDING:
                self.cancel_order(id)

    def order_client_extensions(self, order_id, client_id=None, client_tag=None, client_comment=None):
        data = {'client_id': client_id, 'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)
        response = api.order.set_client_extensions(self.account_id, str(order_id), **kwargs)
        transactions = self._process_order_response(response, 'ORDER_CLIENT_EXTENSIONS')

        return transactions

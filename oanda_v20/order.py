import logging
from decimal import Decimal, ROUND_HALF_UP

from v20.transaction import StopLossDetails, ClientExtensions, TakeProfitDetails, TrailingStopLossDetails
from oanda_v20.base import api, EntityBase
from oanda_v20.common.logger import log_error
from oanda_v20.common.prints import print_orders
from oanda_v20.common.view import print_entity, print_response_entity
from oanda_v20.common.convertor import get_symbol, lots_to_units
from oanda_v20.common.constants import TransactionName, OrderType, OrderPositionFill, TimeInForce, OrderTriggerCondition
import settings

logger = logging.getLogger(__name__)


class OrderMixin(EntityBase):

    # order list
    def _process_orders(self, response):
        orders = response.get("orders", "200")
        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'LIST_ORDER')
            return False, response.body.get('errorMessage')

        if len(orders) == 0:
            logger.debug("Account {} has no pending Orders to cancel".format(
                self.account_id
            ))
        for order in orders:
            self.orders[order.id] = order

        if settings.DEBUG:
            print_orders(orders)
        return True, orders

    def list_order(self, ids=None, state=None, instrument=None, count=None, beforeID=None):
        response = api.order.list(self.account_id, ids, state, instrument, count, beforeID)
        return self._process_orders(response)

    def list_pending_order(self):
        response = api.order.list_pending(self.account_id)
        return self._process_orders(response)

    # order creation
    def _process_order_paramters(self, **kwargs):
        data = {}
        instrument = get_symbol(kwargs['instrument'])
        pip_unit = self.get_pip_unit(instrument)

        if 'instrument' in kwargs:
            data['instrument'] = instrument

        if 'lots' in kwargs:
            units = lots_to_units(kwargs['lots'], kwargs['side'])
            data['units'] = str(units)

        if 'type' in kwargs:
            data['type'] = kwargs['type']

        if 'timeInForce' in kwargs:
            data['timeInForce'] = kwargs['timeInForce'] or TimeInForce.FOK

        if 'priceBound' in kwargs:
            data['priceBound'] = str(kwargs['priceBound'])

        if 'price' in kwargs:
            data['price'] = str(kwargs['price'])

        if 'positionFill' in kwargs:
            data['positionFill'] = kwargs['positionFill'] or OrderPositionFill.DEFAULT

        if 'client_id' in kwargs or 'client_tag' in kwargs or 'client_comment' in kwargs:
            data['tradeClientExtensions'] = ClientExtensions(id=kwargs['client_id'],
                                                             tag=kwargs['client_tag'],
                                                             comment=kwargs['client_comment'])

        if 'take_profit_price' in kwargs:
            data['takeProfitOnFill'] = TakeProfitDetails(
                price=str(kwargs['take_profit_price']),
                clientExtensions=data['tradeClientExtensions']
            )

        if 'stop_loss_pip' in kwargs:
            stop_loss_price = pip_unit * Decimal(str(kwargs['stop_loss_pip']))
            data['stopLossOnFill'] = StopLossDetails(distance=str(stop_loss_price),
                                                     clientExtensions=data['tradeClientExtensions'])

        if 'trailing_pip' in kwargs:
            trailing_distance_price = pip_unit * Decimal(str(kwargs['trailing_pip']))
            data['trailingStopLossOnFill'] = TrailingStopLossDetails(distance=str(trailing_distance_price),
                                                                     clientExtensions=data['tradeClientExtensions'])

        if 'trigger_condition' in kwargs:
            data['triggerCondition'] = kwargs['trigger_condition'] or OrderTriggerCondition.DEFAULT

        if 'gtd_time' in kwargs:
            # todo confirm gtdTime format
            data['gtdTime'] = str(kwargs['gtd_time'])

        return data

    def _process_order_response(self, response, func_name):
        if response.status < 200 or response.status > 299:
            log_error(logger, response, func_name)
            return False, response.body.get('errorMessage')

        transactions = []
        for name in TransactionName.all():
            try:
                transaction = response.get(name, "200")
                transactions.append(transaction)
            except:
                pass

        if settings.DEBUG:
            for t in transactions:
                print_entity(t, title=t.__class__.__name__)
                print('')
        return True, transactions

    def create_order(self):
        pass

    def get_order(self, order_id):
        response = api.order.get(self.account_id, order_id)
        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'GET_ORDER')
            return False, response.body.get('errorMessage')

        order = response.get("order", "200")
        self.orders[order.id] = order

        if settings.DEBUG:
            print_orders([order])
        return True, order

    def market_if_touched(self):
        pass

    def limit_order(self, instrument, side, price,
                    lots=0.1, type=OrderType.LIMIT, timeInForce=TimeInForce.GTC,
                    positionFill=OrderPositionFill.DEFAULT,
                    trigger_condition=OrderTriggerCondition.DEFAULT,
                    gtd_time=None,
                    take_profit_price=None,
                    stop_loss_pip=None,
                    trailing_pip=None,
                    client_id=None, client_tag=None, client_comment=None):
        data = {'instrument': instrument, 'side': side, 'lots': lots, 'type': type, 'timeInForce': timeInForce,
                'price': price, 'positionFill': positionFill, 'take_profit_price': take_profit_price,
                'trigger_condition': trigger_condition, 'gtd_time': gtd_time,
                'stop_loss_pip': stop_loss_pip, 'trailing_pip': trailing_pip, 'client_id': client_id,
                'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)

        response = self.api.order.limit(self.account_id, **kwargs)

        success, transactions = self._process_order_response(response, 'LIMIT_ORDER')

        return success, transactions

    def stop_order(self, instrument, side, price,
                    lots=0.1, type=OrderType.LIMIT, timeInForce=TimeInForce.GTC,
                    positionFill=OrderPositionFill.DEFAULT,priceBound=None,
                    trigger_condition=OrderTriggerCondition.DEFAULT,
                    gtd_time=None,
                    take_profit_price=None,
                    stop_loss_pip=None,
                    trailing_pip=None,
                    client_id=None, client_tag=None, client_comment=None):
        data = {'instrument': instrument, 'side': side, 'lots': lots, 'type': type, 'timeInForce': timeInForce,
                'price': price, 'positionFill': positionFill, 'take_profit_price': take_profit_price,
                'trigger_condition': trigger_condition, 'gtd_time': gtd_time,'priceBound': priceBound,
                'stop_loss_pip': stop_loss_pip, 'trailing_pip': trailing_pip, 'client_id': client_id,
                'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)

        response = self.api.order.stop(self.account_id, **kwargs)

        success, transactions = self._process_order_response(response, 'STOP_ORDER')

        return success, transactions

    def market_order(self, instrument, side,
                     lots=0.1, type=OrderType.MARKET, timeInForce=TimeInForce.FOK,
                     priceBound=None, positionFill=OrderPositionFill.DEFAULT,
                     take_profit_price=None,
                     stop_loss_pip=None,
                     trailing_pip=None,
                     client_id=None, client_tag=None, client_comment=None):

        data = {'instrument': instrument, 'side': side, 'lots': lots, 'type': type, 'timeInForce': timeInForce,
                'priceBound': priceBound, 'positionFill': positionFill, 'take_profit_price': take_profit_price,
                'stop_loss_pip': stop_loss_pip, 'trailing_pip': trailing_pip, 'client_id': client_id,
                'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)

        response = self.api.order.market(self.account_id, **kwargs)

        success, transactions = self._process_order_response(response, 'MARKET_ORDER')

        # todo fail: ORDER_CANCEL,MARKET_ORDER_REJECT
        # todo success:MARKET_ORDER + ORDER_FILL
        return True, transactions

    # cancel
    def cancel_order(self, order_id):
        response = api.order.cancel(self.account_id, order_id)

        print("Response: {} ({})".format(response.status, response.reason))

        if response.status < 200 or response.status > 299:
            transaction = response.get('orderCancelRejectTransaction', "404")
            if settings.DEBUG:
                print_entity(transaction, title='Order Cancel Reject')
            return False, transaction

        transaction = response.get('orderCancelTransaction', "200")
        if settings.DEBUG:
            print_entity(transaction, title='Order Canceled')

        return True, transaction

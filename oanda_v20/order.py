import logging
from decimal import Decimal, ROUND_HALF_UP

from v20.transaction import StopLossDetails, ClientExtensions, TakeProfitDetails, TrailingStopLossDetails
from oanda_v20.base import api, EntityBase
from oanda_v20.common.logger import log_error
from oanda_v20.common.prints import print_orders
from oanda_v20.common.view import print_entity, print_response_entity
from oanda_v20.common.convertor import get_symbol, lots_to_units
from oanda_v20.common.constants import TransactionName, OrderType, OrderPositionFill, TimeInForce
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

    def market_order(self, instrument, side,
                     lots=0.1, type=OrderType.MARKET, timeInForce=TimeInForce.FOK,
                     priceBound=None, positionFill=OrderPositionFill.DEFAULT,
                     take_profit_price=None,
                     stop_loss_pip=None,
                     trailing_pip=None,
                     client_id=None, client_tag=None, client_comment=None):
        instrument = get_symbol(instrument)
        units = lots_to_units(lots, side)
        pip_unit = self.get_pip_unit(instrument)

        # client extension
        client_args = {'id': client_id, 'tag': client_tag, 'comment': client_comment}
        if any(client_args.values()):
            tradeClientExtensions = ClientExtensions(**client_args)
        else:
            tradeClientExtensions = None

        # stop loss
        if stop_loss_pip:
            stop_loss_price = pip_unit * Decimal(str(stop_loss_pip))
            stop_loss_details = StopLossDetails(distance=str(stop_loss_price), clientExtensions=tradeClientExtensions)
        else:
            stop_loss_details = None

        if take_profit_price:
            take_profit_detail = TakeProfitDetails(price=str(take_profit_price), clientExtensions=tradeClientExtensions)
        else:
            take_profit_detail = None

        if trailing_pip:
            trailing_distance_price = pip_unit * Decimal(str(trailing_pip))
            trailing_details = TrailingStopLossDetails(distance=str(trailing_distance_price),
                                                       clientExtensions=tradeClientExtensions)
        else:
            trailing_details = None

        response = self.api.order.market(
            self.account_id,
            instrument=instrument, units=str(units), type=type, timeInForce=timeInForce,
            priceBound=priceBound, positionFill=positionFill,
            takeProfitOnFill=take_profit_detail,
            stopLossOnFill=stop_loss_details,
            trailingStopLossOnFill=trailing_details,
            tradeClientExtensions=tradeClientExtensions
        )

        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'MARKET_ORDER')
            return False, response.body.get('errorMessage')

        transactions = []
        for name in TransactionName.all():
            try:
                transaction = response.get(name, "200")
                transactions.append(transaction)
            except:
                pass
        for t in transactions:
            print_entity(t, title=t.__class__.__name__)
            print('')

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

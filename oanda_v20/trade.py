import logging
from decimal import Decimal, ROUND_HALF_UP
from oanda_v20.common.convertor import get_symbol

from v20.transaction import StopLossDetails, ClientExtensions, TakeProfitDetails, TrailingStopLossDetails
from oanda_v20.base import api, EntityBase
from oanda_v20.common.logger import log_error
from oanda_v20.common.prints import print_orders
from oanda_v20.common.view import print_entity, print_response_entity
from oanda_v20.common.convertor import get_symbol, lots_to_units
from oanda_v20.common.constants import TransactionName, OrderType, OrderPositionFill, TimeInForce, OrderTriggerCondition
import settings

logger = logging.getLogger(__name__)


class TradeMixin(EntityBase):

    # update SL and TP
    def take_profit(self, trade_id, price, client_trade_id=None,
                    timeInForce=TimeInForce.GTC, gtd_time=None,
                    trigger_condition=OrderTriggerCondition.DEFAULT,
                    client_id=None, client_tag=None, client_comment=None):
        data = {'trade_id': trade_id, 'price': price, 'client_trade_id': client_trade_id,
                'type': OrderType.TAKE_PROFIT, 'timeInForce': timeInForce,
                'trigger_condition': trigger_condition, 'gtd_time': gtd_time,
                'client_id': client_id, 'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)

        response = self.api.order.take_profit(self.account_id, **kwargs)

        success, transactions = self._process_order_response(response, 'TAKE_PROFIT')

        return success, transactions

    def stop_loss(self, trade_id, distance=None, price=None, client_trade_id=None,
                  timeInForce=TimeInForce.GTC, gtd_time=None,
                  trigger_condition=OrderTriggerCondition.DEFAULT,
                  guaranteed=None,
                  client_id=None, client_tag=None, client_comment=None):
        data = {'trade_id': trade_id, 'client_trade_id': client_trade_id,
                'price': price, 'distance': distance,
                'type': OrderType.STOP_LOSS, 'timeInForce': timeInForce, 'guaranteed': guaranteed,
                'trigger_condition': trigger_condition, 'gtd_time': gtd_time,
                'client_id': client_id, 'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)

        response = self.api.order.stop_loss(self.account_id, **kwargs)

        success, transactions = self._process_order_response(response, 'STOP_LOSS')

        return success, transactions

    def trailing_stop_loss(self, trade_id, distance=None, client_trade_id=None,
                           timeInForce=TimeInForce.GTC, gtd_time=None,
                           trigger_condition=OrderTriggerCondition.DEFAULT,
                           client_id=None, client_tag=None, client_comment=None):
        data = {'trade_id': trade_id, 'client_trade_id': client_trade_id,
                'distance': distance,
                'type': OrderType.TRAILING_STOP_LOSS, 'timeInForce': timeInForce,
                'trigger_condition': trigger_condition, 'gtd_time': gtd_time,
                'client_id': client_id, 'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)

        response = self.api.order.trailing_stop_loss(self.account_id, **kwargs)

        success, transactions = self._process_order_response(response, 'TRAILING_STOP_LOSS')

        return success, transactions

    def trade_client_extensions(self, trade_id, client_id=None, client_tag=None, client_comment=None):
        data = {'client_id': client_id, 'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)
        response = api.trade.set_client_extensions(self.account_id, trade_id, **kwargs)
        success, transactions = self._process_order_response(response, 'TRADE_CLIENT_EXTENSIONS')

        return success, transactions

import logging
from decimal import Decimal, ROUND_HALF_UP

from mt4.constants import OrderSide
from oanda_v20.common.convertor import get_symbol

from v20.transaction import StopLossDetails, ClientExtensions, TakeProfitDetails, TrailingStopLossDetails
from oanda_v20.base import api, EntityBase
from oanda_v20.common.logger import log_error
from oanda_v20.common.prints import print_trades
from oanda_v20.common.view import print_entity, print_response_entity
from oanda_v20.common.convertor import get_symbol, lots_to_units
from oanda_v20.common.constants import TransactionName, OrderType, OrderPositionFill, TimeInForce, OrderTriggerCondition
import settings

logger = logging.getLogger(__name__)


class TradeMixin(EntityBase):

    # list
    def _process_trades(self, response):

        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'LIST_TRADE')
            return False, response.body.get('errorMessage')

        trades = response.get("trades", "200")
        for trade in trades:
            self.trades[trade.id] = trade

        if settings.DEBUG:
            print_trades(trades)
        return True, trades

    def list_trade(self, ids=None, state=None, instrument=None, count=20, beforeID=None):
        data = {}
        if ids:
            data['ids'] = ids
        if state:
            data['state'] = state
        if instrument:
            data['instrument'] = instrument
        if count:
            data['count'] = count
        if beforeID:
            data['beforeID'] = beforeID

        response = api.trade.list(self.account_id, **data)
        return self._process_trades(response)

    def list_open_trade(self):
        response = api.trade.list_open(self.account_id)
        return self._process_trades(response)

    def get_trade(self, trade_id):
        response = api.trade.get(self.account_id, str(trade_id))
        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'GET_TRADE')
            return None

        trade = response.get("trade", "200")
        self.trades[trade.id] = trade

        if settings.DEBUG:
            print_trades([trade])
        return trade

    def close(self, trade_id, lots='ALL'):
        # units : (string, default=ALL)
        # Indication of how much of the Trade to close. Either the string “ALL”
        # (indicating that all of the Trade should be closed), or a DecimalNumber
        # representing the number of units of the open Trade to Close using a
        # TradeClose MarketOrder. The units specified must always be positive, and
        # the magnitude of the value cannot exceed the magnitude of the Trade’s
        # open units.
        if lots != 'ALL':
            units = str(lots_to_units(lots, OrderSide.BUY))
        else:
            units = 'ALL'

        response = api.trade.close(self.account_id, trade_id, units=str(units))
        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'CLOSE_TRADE')
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
        # orderCreateTransaction, orderFillTransaction, orderCancelTransaction
        return True, transactions

    def trade_client_extensions(self, trade_id, client_id=None, client_tag=None, client_comment=None):
        data = {'client_id': client_id, 'client_tag': client_tag, 'client_comment': client_comment}
        kwargs = self._process_order_paramters(**data)
        response = api.trade.set_client_extensions(self.account_id, trade_id, **kwargs)
        success, transactions = self._process_order_response(response, 'TRADE_CLIENT_EXTENSIONS')

        return success, transactions

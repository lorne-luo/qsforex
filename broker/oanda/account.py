import logging
from decimal import Decimal

import broker.oanda.common.view as common_view
from broker.base import BrokerAccount
from broker.oanda.base import SingletonAPIContext
from broker.oanda.common.constants import OANDA_ENVIRONMENTS
from broker.oanda.common.convertor import get_symbol
from broker.oanda.common.logger import log_error
from broker.oanda.common.prints import print_positions_map, print_orders_map, print_trades_map
from broker.oanda.instrument import InstrumentMixin
from broker.oanda.order import OrderMixin
from broker.oanda.position import PositionMixin
from broker.oanda.price import PriceMixin
from broker.oanda.trade import TradeMixin

logger = logging.getLogger(__name__)


class OANDA(PositionMixin, OrderMixin, TradeMixin, InstrumentMixin, PriceMixin, BrokerAccount):
    """
    An Account object is a wrapper for the Account entities fetched from the
    v20 REST API. It is used for caching and updating Account state.
    """
    broker = 'OANDA'

    # all_currencies=['name', 'type', 'displayName', 'pipLocation', 'displayPrecision', 'tradeUnitsPrecision', 'minimumTradeSize', 'maximumTrailingStopDistance', 'minimumTrailingStopDistance', 'maximumPositionSize', 'maximumOrderUnits', 'marginRate', 'commission']
    default_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'NZD_USD', 'USD_CNH', 'XAU_USD']

    def setup_api(self, type, access_token, application_name):
        self.type = type
        hostname = OANDA_ENVIRONMENTS["api"][type]
        stream_hostname = OANDA_ENVIRONMENTS["streaming"][type]
        self.api = SingletonAPIContext(hostname=hostname, token=access_token, application=application_name)
        self.stream_api = SingletonAPIContext(hostname=stream_hostname, token=access_token,
                                              application=application_name)

    def __init__(self, type, account_id, access_token, application_name=None, transaction_cache_depth=100,
                 *args, **kwargs):
        """
        Create a new Account wrapper
        Args:
            account: a v20.account.Account fetched from the server
        """
        self.account_id = account_id
        self.access_token = access_token
        self.setup_api(type, access_token, application_name)
        super(OANDA, self).__init__(*args, **kwargs)

        #
        # The collection of Trades open in the Account
        #
        response = self.api.account.get(account_id)
        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'GET_ACCOUNT')

        account = response.get("account", "200")

        for trade in getattr(account, "trades", []):
            self.trades[trade.id] = trade

        setattr(account, "trades", None)

        #
        # The collection of Orders pending in the Account
        #

        for order in getattr(account, "orders", []):
            self.orders[order.id] = order

        setattr(account, "orders", None)

        #
        # Map from OrderID -> OrderState. Order State is tracked for
        # TrailingStopLoss orders, and includes the trailingStopValue
        # and triggerDistance
        #
        self.order_states = {}

        #
        # Teh collection of Positions open in the Account
        #
        self.positions = {}

        for position in getattr(account, "positions", []):
            self.positions[position.instrument] = position

        setattr(account, "positions", None)

        #
        # Keep a cache of the last self.transaction_cache_depth Transactions
        #
        self.transaction_cache_depth = transaction_cache_depth
        self.transactions = []

        #
        # The Account details
        #
        self.details = account

        self.list_instruments()
        self.base_leverage = int(1 / self.instruments['EUR_USD']['marginRate'])

    def __str__(self):
        return '%s # %s' % (self.details.id, self.details.alias)

    def dump(self):
        """
        Print out the whole Account state
        """

        common_view.print_entity(
            self.details,
            title=self.details.title()
        )

        print("")

        print_positions_map(self.positions)

        print_orders_map(self.orders)

        print_trades_map(self.trades)

    def get_position(self, instrument):
        """Fetch an open Position"""
        instrument = get_symbol(instrument)
        return self.positions.get(instrument, None)

    def get_detail(self, key):
        return getattr(self.details, key)

    def apply_changes(self, changes):
        """
        Update the Account state with a set of changes provided by the server.

        Args:
            changes: a v20.account.AccountChanges object representing the 
                     changes that have been made to the Account
        """

        for order in changes.ordersCreated:
            logger.info("[Order Created] {}".format(order.title()))
            self.orders[order.id] = order

        for order in changes.ordersCancelled:
            logger.info("[Order Cancelled] {}".format(order.title()))
            self.orders.pop(order.id, None)

        for order in changes.ordersFilled:
            logger.info("[Order Filled] {}".format(order.title()))
            self.orders.pop(order.id, None)

        for order in changes.ordersTriggered:
            logger.info("[Order Triggered] {}".format(order.title()))
            self.orders.pop(order.id, None)

        for trade in changes.tradesOpened:
            logger.info("[Trade Opened] {}".format(trade.title()))
            self.trades[trade.id] = trade

        for trade in changes.tradesReduced:
            logger.info("[Trade Reduced] {}".format(trade.title()))
            self.trades[trade.id] = trade

        for trade in changes.tradesClosed:
            logger.info("[Trade Closed] {}".format(trade.title()))
            self.trades.pop(trade.id, None)

        for position in changes.positions:
            logger.info("[Position Changed] {}".format(position.instrument))
            self.positions[position.instrument] = position

        for transaction in changes.transactions:
            logger.info("[Transaction] {}".format(transaction.title()))

            self.transactions.append(transaction)

            if len(self.transactions) > self.transaction_cache_depth:
                self.transactions.pop(0)

    def apply_trade_states(self, trade_states):
        """
        Update state for open Trades

        Args:
            trade_states: A list of v20.trade.CalculatedTradeState objects
                          representing changes to the state of open Trades

        """
        for trade_state in trade_states:
            trade = self.get_trade(trade_state.id)

            if trade is None:
                continue

            for field in trade_state.fields():
                setattr(trade, field.name, field.value)

    def apply_position_states(self, position_states):
        """
        Update state for all Positions

        Args:
            position_states: A list of v20.trade.CalculatedPositionState objects
                             representing changes to the state of open Position

        """

        for position_state in position_states:
            position = self.get_position(position_state.instrument)

            if position is None:
                continue

            position.unrealizedPL = position_state.netUnrealizedPL
            position.long.unrealizedPL = position_state.longUnrealizedPL
            position.short.unrealizedPL = position_state.shortUnrealizedPL

    def apply_order_states(self, order_states):
        """
        Update state for all Orders

        Args:
            order_states: A list of v20.order.DynamicOrderState objects
                          representing changes to the state of pending Orders
        """

        for order_state in order_states:
            order = self.get_order(order_state.id)

            if order is None:
                continue

            order.trailingStopValue = order_state.trailingStopValue

            self.order_states[order.id] = order_state

    def apply_state(self, state):
        """
        Update the state of an Account 

        Args:
            state: A v20.account.AccountState object representing changes to
                   the Account's trades, positions, orders and state.
        """

        #
        # Update Account details from the state
        #
        def update_attribute(dest, name, value):
            """
            Set dest[name] to value if it exists and is not None
            """
            if hasattr(dest, name) and \
                    getattr(dest, name) is not None:
                setattr(dest, name, value)

        for field in state.fields():
            update_attribute(self.details, field.name, field.value)

        self.apply_trade_states(state.trades)

        self.apply_position_states(state.positions)

        self.apply_order_states(state.orders)

    def pull(self):
        """pull newest states"""
        response = self.api.account.changes(
            self.account_id,
            sinceTransactionID=self.details.lastTransactionID
        )

        self.apply_changes(
            response.get("changes", "200")
        )

        self.apply_state(
            response.get("state", "200")
        )

        self.details.lastTransactionID = response.get("lastTransactionID", "200")

    @property
    def margin_level(self):
        if self.details.marginUsed:
            level = self.details.NAV / self.details.marginUsed * self.base_leverage

            return Decimal(level).quantize(Decimal('0.01'))
        return 0

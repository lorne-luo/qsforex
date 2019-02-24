import logging
from decimal import Decimal, ROUND_HALF_UP

from v20.transaction import StopLossDetails, TakeProfitDetails, TrailingStopLossDetails, ClientExtensions

import oanda_v20.common.view as common_view
from mt4.constants import OrderSide
from oanda_v20.base import EntityBase
from oanda_v20.common.logger import log_error
from oanda_v20.common.constants import TransactionName, OrderType, TimeInForce, OrderPositionFill
from oanda_v20.common.convertor import get_symbol, lots_to_units
from oanda_v20.instrument import InstrumentMixin
from oanda_v20.order import OrderMixin
from oanda_v20.position import PositionMixin
from oanda_v20.common.prints import print_positions_map, print_orders_map, print_trades_map
import settings

logger = logging.getLogger(__name__)


class Account(EntityBase):
    """
    An Account object is a wrapper for the Account entities fetched from the
    v20 REST API. It is used for caching and updating Account state.
    """
    _instruments = {}
    order_states = {}
    positions = {}
    transactions = []
    trades = {}
    orders = {}
    details = None

    def __init__(self, account_id, transaction_cache_depth=100):
        """
        Create a new Account wrapper

        Args:
            account: a v20.account.Account fetched from the server
        """

        #
        # The collection of Trades open in the Account
        #
        self.account_id = account_id
        response = self.api.account.get(account_id)
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

    def get_trade(self, id):
        """Fetch an open Trade"""
        return self.trades.get(id, None)

    def get_order(self, id):
        """Fetch a pending Order"""

        return self.orders.get(id, None)

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
            response.get(
                "changes",
                "200"
            )
        )

        self.apply_state(
            response.get(
                "state",
                "200"
            )
        )

        self.details.lastTransactionID = response.get(
            "lastTransactionID",
            "200"
        )

    # ===================== INSTRUMENT & PRICE =====================
    @property
    def instruments(self):
        if self._instruments:
            return self._instruments
        else:
            return self.list_instruments()

    def list_instruments(self):
        """get all avaliable instruments"""
        response = self.api.account.instruments(self.account_id)
        instruments = response.get("instruments", "200")
        if not len(instruments):
            return

        # all_keys=['name', 'type', 'displayName', 'pipLocation', 'displayPrecision', 'tradeUnitsPrecision', 'minimumTradeSize', 'maximumTrailingStopDistance', 'minimumTrailingStopDistance', 'maximumPositionSize', 'maximumOrderUnits', 'marginRate', 'commission']
        columns = ['name', 'type', 'displayName', 'pipLocation', 'displayPrecision', 'marginRate']
        # all_currencies=[i.name for i in instruments]
        currencies = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'NZD_USD', 'USD_CNH', 'XAU_USD']

        data = {}
        for i in instruments:
            if i.name in currencies:
                data[i.name] = {'name': i.name,
                                'type': i.type,
                                'displayName': i.displayName,
                                'pipLocation': i.pipLocation,
                                'pip': 10 ** i.pipLocation,
                                'displayPrecision': i.displayPrecision,
                                'marginRateDisplay': "{:.0f}:1".format(1.0 / float(i.marginRate)),
                                'marginRate': i.marginRate, }

        self._instruments = data
        return self._instruments

    def get_pip_unit(self, instrument):
        """get pip unit for instrument"""
        instrument = get_symbol(instrument)
        try:
            unit = self.instruments[instrument].get('pip')
            return Decimal(str(unit))
        except KeyError:
            return None

    def get_pip(self, value, instrument):
        """calculate pip"""
        instrument = get_symbol(instrument)
        unit = self.get_pip_unit(instrument)
        value = Decimal(str(value))
        place_location = self.instruments[instrument]['displayPrecision'] + self.instruments[instrument]['pipLocation']
        places = 10 ** (place_location * -1)
        return (value / unit).quantize(Decimal(str(places)), rounding=ROUND_HALF_UP)

    def calculate_price(self, base_price, side, pip, instrument):
        instrument = get_symbol(instrument)
        pip_unit = self.get_pip_unit(instrument)
        base_price = Decimal(str(base_price))
        pip = Decimal(str(pip))

        if side == OrderSide.BUY:
            return base_price + pip * pip_unit
        elif side == OrderSide.SELL:
            return base_price - pip * pip_unit

    # ===================== POSITION =====================
    def pull_position(self, instrument):
        """pull position by instrument"""
        instrument = get_symbol(instrument)
        response = self.api.position.get(self.account_id, instrument)

        if response.status >= 200:
            last_transaction_id = response.list('lastTransactionID', [])
            position = response.get('position', None)
            if position:
                self.positions[position.instrument] = position

            return True, position
        else:
            log_error(logger, response, 'QEURY_POSITION')
            return False, response.body['errorMessage']

    def list_all_positions(self):
        response = self.api.position.close(
            self.account_id,
        )
        if response.status >= 200:
            last_transaction_id = response.list('lastTransactionID', [])
            positions = response.list('positions', [])
            for position in positions:
                self.positions[position.instrument] = position

            return True, positions
        else:
            log_error(logger, response, 'LIST_ALL_POSITION')
            return False, response.body['errorMessage']

    def list_open_positions(self):
        response = self.api.position.close(
            self.account_id,
        )
        if response.status >= 200:
            last_transaction_id = response.list('lastTransactionID', [])
            positions = response.list_open('positions', [])
            for position in positions:
                self.positions[position.instrument] = position
            return True, positions
        else:
            log_error(logger, response, 'LIST_OPEN_POSITION')
            return False, response.body['errorMessage']

    def close_all_position(self):
        instruments = self.positions.keys()
        logger.error('[CLOSE_ALL_POSITIONS] Start.')
        for i in instruments:
            self.close_position(i, 'ALL', 'ALL')

    def close_position(self, instrument, longUnits='ALL', shortUnits='ALL'):
        instrument = get_symbol(instrument)

        response = self.api.position.close(
            self.account_id,
            instrument,
            longUnits=longUnits,
            shortUnits=shortUnits
        )

        if response.status >= 200:
            longOrderCreateTransaction = response.get('longOrderCreateTransaction', None)
            longOrderFillTransaction = response.get('longOrderFillTransaction', None)
            longOrderCancelTransaction = response.get('longOrderCancelTransaction', None)
            shortOrderCreateTransaction = response.get('shortOrderCreateTransaction', None)
            shortOrderFillTransaction = response.get('shortOrderFillTransaction', None)
            shortOrderCancelTransaction = response.get('shortOrderCancelTransaction', None)
            relatedTransactionIDs = response.get('relatedTransactionIDs', None)
            lastTransactionID = response.get('lastTransactionID', None)
            print(longOrderCreateTransaction.__dict__)
            print(longOrderFillTransaction.__dict__)
            print(longOrderCancelTransaction.__dict__)
            print(shortOrderCreateTransaction.__dict__)
            print(shortOrderFillTransaction.__dict__)
            print(shortOrderCancelTransaction.__dict__)
            print(relatedTransactionIDs.__dict__)
            print(lastTransactionID)
            return True, 'done'
        else:
            log_error(logger, response, 'CLOSE_POSITION')
            return False, response.body['errorMessage']

    # ================= ORDER =================
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

        take_profit_detail = TakeProfitDetails(price=str(take_profit_price), clientExtensions=tradeClientExtensions)

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

        if response.status >= 200:
            transactions = []
            for name in TransactionName.all():
                try:
                    transaction = response.get(name, None)
                    transactions.append(transaction)
                except:
                    pass
            for t in transactions:
                common_view.print_entity(t, title=t.__class__.__name__)
                print('')

            # todo fail: ORDER_CANCEL,MARKET_ORDER_REJECT
            # todo success:MARKET_ORDER + ORDER_FILL
            return transactions
        else:
            log_error(logger, response, 'MARKET_ORDER')
            return False, response.body.get('errorMessage')

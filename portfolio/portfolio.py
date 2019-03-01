"""
takes SignalEvents from the Queue and generates OrderEvents that get added to the Queue.
"""
from __future__ import print_function

from copy import deepcopy
from decimal import Decimal, getcontext, ROUND_HALF_DOWN
import logging
import os

import pandas as pd

from qsforex.event.event import OrderEvent
from qsforex.performance.performance import create_drawdowns
from qsforex.portfolio.position import Position
from qsforex.utils.file import create_folder
from qsforex import settings

from mt4.constants import pip
from oanda_v20.account import Account
from oanda_v20.base import SingletonAPIContext
from oanda_v20.common.constants import OrderType
from oanda_v20.common.convertor import lots_to_units, get_symbol, units_to_lots
from settings import OANDA_ENVIRONMENTS


class Portfolio(object):
    def __init__(
            self, ticker, events, base_currency=settings.BASE_CURRENCY,
            leverage=20, equity=settings.EQUITY,
            risk_per_trade=Decimal("0.02"), backtest=True
    ):
        self.ticker = ticker
        self.events = events
        self.base_currency = base_currency
        self.leverage = leverage
        self.equity = equity
        self.balance = deepcopy(self.equity)
        self.risk_per_trade = risk_per_trade
        self.backtest = backtest
        self.trade_units = self.calc_risk_position_size()
        self.positions = {}
        if self.backtest:
            self.backtest_file = self.create_equity_file()
        self.logger = logging.getLogger(__name__)

    def calc_risk_position_size(self):
        return self.equity * self.risk_per_trade

    def add_new_position(
            self, position_type, currency_pair, units, ticker
    ):
        ps = Position(
            self.base_currency, position_type,
            currency_pair, units, ticker
        )
        self.positions[currency_pair] = ps

    def add_position_units(self, currency_pair, units):
        if currency_pair not in self.positions:
            return False
        else:
            ps = self.positions[currency_pair]
            ps.add_units(units)
            return True

    def remove_position_units(self, currency_pair, units):
        if currency_pair not in self.positions:
            return False
        else:
            ps = self.positions[currency_pair]
            pnl = ps.remove_units(units)
            self.balance += pnl
            return True

    def close_position(self, currency_pair):
        if currency_pair not in self.positions:
            return False
        else:
            ps = self.positions[currency_pair]
            pnl = ps.close_position()
            self.balance += pnl
            del [self.positions[currency_pair]]
            return True

    def create_equity_file(self):
        filename = "backtest.csv"
        filepath = os.path.join(settings.OUTPUT_RESULTS_DIR, filename)
        create_folder(filepath)
        out_file = open(filepath, "w")

        header = "Timestamp,Balance"
        for pair in self.ticker.pairs:
            header += ",%s" % pair
        header += "\n"
        out_file.write(header)
        if self.backtest:
            print(header[:-2])
        return out_file

    def output_results(self):
        # Closes off the Backtest.csv file so it can be 
        # read via Pandas without problems
        self.backtest_file.close()

        in_filename = "backtest.csv"
        out_filename = "equity.csv"
        in_file = os.path.join(settings.OUTPUT_RESULTS_DIR, in_filename)
        out_file = os.path.join(settings.OUTPUT_RESULTS_DIR, out_filename)

        # Create equity curve dataframe
        df = pd.read_csv(in_file, index_col=0)
        df.dropna(inplace=True)
        df["Total"] = df.sum(axis=1)
        df["Returns"] = df["Total"].pct_change()
        df["Equity"] = (1.0 + df["Returns"]).cumprod()

        # Create drawdown statistics
        drawdown, max_dd, dd_duration = create_drawdowns(df["Equity"])
        df["Drawdown"] = drawdown
        df.to_csv(out_file, index=True)

        print("Simulation complete and results exported to %s" % out_filename)

    def update_portfolio(self, tick_event):
        """
        This updates all positions ensuring an up to date
        unrealised profit and loss (PnL).
        """
        currency_pair = tick_event.instrument
        if currency_pair in self.positions:
            ps = self.positions[currency_pair]
            ps.update_position_price()
        if self.backtest:
            out_line = "%s,%s" % (tick_event.time, self.balance)
            for pair in self.ticker.pairs:
                if pair in self.positions:
                    out_line += ",%s" % self.positions[pair].profit_base
                else:
                    out_line += ",0.00"
            out_line += "\n"
            print(out_line[:-2])
            self.backtest_file.write(out_line)

    def execute_signal(self, signal_event):
        # Check that the prices ticker contains all necessary
        # currency pairs prior to executing an order
        execute = True
        tp = self.ticker.prices
        for pair in tp:
            if tp[pair]["ask"] is None or tp[pair]["bid"] is None:
                execute = False

        # All necessary pricing data is available,
        # we can execute
        if execute:
            side = signal_event.side
            currency_pair = signal_event.instrument
            units = int(self.trade_units)
            time = signal_event.time

            # If there is no position, create one
            if currency_pair not in self.positions:
                if side == "buy":
                    position_type = "long"
                else:
                    position_type = "short"
                self.add_new_position(
                    position_type, currency_pair,
                    units, self.ticker
                )

            # If a position exists add or remove units
            else:
                ps = self.positions[currency_pair]

                if side == "buy" and ps.position_type == "long":
                    self.add_position_units(currency_pair, units)

                elif side == "sell" and ps.position_type == "long":
                    if units == ps.units:
                        self.close_position(currency_pair)
                    # TODO: Allow units to be added/removed
                    elif units < ps.units:
                        return
                    elif units > ps.units:
                        return

                elif side == "buy" and ps.position_type == "short":
                    if units == ps.units:
                        self.close_position(currency_pair)
                    # TODO: Allow units to be added/removed
                    elif units < ps.units:
                        return
                    elif units > ps.units:
                        return

                elif side == "sell" and ps.position_type == "short":
                    self.add_position_units(currency_pair, units)

            order = OrderEvent(currency_pair, units, OrderType.MARKET, side)
            self.events.put(order)

            self.logger.info("Portfolio Balance: %s" % self.balance)
        else:
            self.logger.info("Unable to execute order as price data was insufficient.")


class OandaV20Portfolio(object):
    def __init__(
            self, type, access_token, account_id, queue,
            leverage=None, equity=None, base_currency='USD',
            risk_ratio=Decimal("0.05")
    ):
        self.queue = queue
        self.account_id = account_id
        self.account = Account(type=type, account_id=account_id, access_token=access_token)
        self.leverage = leverage or int(1 / self.account.instruments['EUR_USD']['marginRate'])

        self.base_currency = base_currency or self.account.details.currency
        self.risk_ratio = risk_ratio  # risk_per_trade
        self.positions = {}
        self.margin_rate = Decimal(str(self.account.details.marginRate))
        self.logger = logging.getLogger(__name__)

    @property
    def alias(self):
        return self.account.details.alias

    @property
    def equity(self):
        return Decimal(str(self.account.details.NAV))

    @property
    def balance(self):
        return Decimal(str(self.account.details.balance))

    @property
    def open_trade_count(self):
        return self.account.details.openTradeCount

    @property
    def pending_order_count(self):
        return self.account.details.pendingOrderCount

    @property
    def margin_used(self):
        return self.account.details.marginUsed

    @property
    def margin_level(self):
        return self.account.margin_level

    def dump(self):
        self.account.dump()

    def trade_units(self, instrument, stop_loss_pips):
        """get max units for this instrument"""
        instrument = get_symbol(instrument)
        pip_unit = pip(instrument)

        risk = self.equity * self.risk_ratio
        value = risk / stop_loss_pips / pip_unit

        if instrument.upper().startswith('USD'):
            price = self.account.get_price(instrument)
            value = value * price
        elif instrument.upper().endswith('USD'):
            pass
        else:
            # cross pair
            raise NotImplementedError

        return int(value / 100) * 100


if __name__ == '__main__':
    from portfolio.portfolio import *
    profile = OandaV20Portfolio('DEMO', settings.ACCESS_TOKEN, '101-011-10496264-002', None)
    units = profile.trade_units('EURUSD', 30)
    print(units)
    print(units_to_lots(units))
    units = profile.trade_units('USDJPY', 30)
    print(units)
    print(units_to_lots(units))

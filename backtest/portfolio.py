import logging
from copy import deepcopy
from datetime import datetime

from strategy import OrderEvent
from decimal import Decimal, getcontext, ROUND_HALF_DOWN

UNIT_RATIO = 100000
LEVERAGE = 100


class Position(object):
    def __init__(self, home_currency, position_type, currency_pair, units, ticker, time=None):
        self.home_currency = home_currency
        self.position_type = position_type
        self.currency_pair = currency_pair
        self.units = units
        self.ticker = ticker
        self.time = time
        self.set_up_currencies()
        self.profit_base = self.calculate_profit_base()
        self.profit_perc = self.calculate_profit_perc()

    def set_up_currencies(self):
        ticker_cur = self.ticker.prices[self.currency_pair]
        if self.position_type == "long":
            self.avg_price = Decimal(str(ticker_cur["ask"]))
            self.cur_price = Decimal(str(ticker_cur["bid"]))
        else:
            self.avg_price = Decimal(str(ticker_cur["bid"]))
            self.cur_price = Decimal(str(ticker_cur["ask"]))

    def calculate_pips(self):
        mult = Decimal("1000")
        if self.position_type == "long":
            mult = Decimal("1")
        elif self.position_type == "short":
            mult = Decimal("-1")
        pips = (mult * (self.cur_price - self.avg_price)).quantize(
            Decimal("0.00001"), ROUND_HALF_DOWN
        )
        return pips

    def calculate_profit_base(self):
        pips = self.calculate_pips()
        ticker_qh = self.ticker.prices[self.currency_pair]
        if self.position_type == "long":
            qh_close = Decimal(str(ticker_qh["bid"]))
        else:
            qh_close = Decimal(str(ticker_qh["ask"]))
        profit = pips * qh_close * Decimal(str(self.units))
        return profit.quantize(
            Decimal("0.00001"), ROUND_HALF_DOWN
        )

    def calculate_profit_perc(self):
        return (self.profit_base / self.units * Decimal("100.00")).quantize(
            Decimal("0.00001"), ROUND_HALF_DOWN
        )

    def update_position_price(self):
        ticker_cur = self.ticker.prices[self.currency_pair]
        if self.position_type == "long":
            self.cur_price = Decimal(str(ticker_cur["bid"]))
        else:
            self.cur_price = Decimal(str(ticker_cur["ask"]))
        self.profit_base = self.calculate_profit_base()
        self.profit_perc = self.calculate_profit_perc()

    def add_units(self, units):
        cp = self.ticker.prices[self.currency_pair]
        if self.position_type == "long":
            add_price = cp["ask"]
        else:
            add_price = cp["bid"]
        new_total_units = self.units + units
        new_total_cost = self.avg_price * self.units + add_price * units
        self.avg_price = new_total_cost / new_total_units
        self.units = new_total_units

    def remove_units(self, units):
        dec_units = Decimal(str(units))
        ticker_quote = self.ticker.prices[self.currency_pair]
        if self.position_type == "long":
            quote_close = ticker_quote["ask"]
        else:
            quote_close = ticker_quote["bid"]
        self.units -= dec_units
        # Calculate PnL
        pnl = self.calculate_pips() * dec_units
        getcontext().rounding = ROUND_HALF_DOWN
        return pnl.quantize(Decimal("0.01"))

    def close_position(self):
        ticker_quote = self.ticker.prices[self.currency_pair]
        if self.position_type == "long":
            quote_close = Decimal(str(ticker_quote["bid"]))
        else:
            quote_close = Decimal(str(ticker_quote["ask"]))
        # Calculate PnL
        pnl = self.calculate_pips() * Decimal(str(self.units))
        getcontext().rounding = ROUND_HALF_DOWN
        return pnl.quantize(Decimal("0.01"))


class Portfolio(object):
    time = None
    trade_count = 0
    win_count = 0
    loss_count = 0

    def __init__(
            self, ticker, events, backtest, base="USD", leverage=1,
            equity=1000000.00, risk_per_trade=0.02,
    ):
        self.ticker = ticker
        self.events = events
        self.base = base
        self.leverage = leverage
        self.equity = equity
        self.balance = deepcopy(self.equity)
        self.risk_per_trade = risk_per_trade
        self.backtest = backtest
        self.trade_units = self.calc_risk_position_size()
        self.positions = {}
        self.logger = logging.getLogger(__name__)

    def calc_risk_position_size(self):
        # the amount size per trade is per 1k
        return self.equity * LEVERAGE * self.risk_per_trade

    def add_new_position(self, position_type, currency_pair, units, time):
        ps = Position(self.base, position_type, currency_pair, units, self.ticker, time)
        self.positions[currency_pair] = ps

    def add_position_units(self, currency_pair, units):
        if currency_pair not in self.positions:
            return False
        else:
            ps = self.positions[currency_pair]
            ps.add_units(units)
            return True

    # TODO allow the removal of units in a position
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
            pnl = float(ps.close_position())
            if pnl > 0:
                self.win_count += 1
            else:
                self.loss_count += 1

            self.balance += pnl
            print('%s -> %s = %s' % (ps.time.strftime('%Y-%m-%d %H:%M'), self.time.strftime('%Y-%m-%d %H:%M'), pnl))
            del [self.positions[currency_pair]]
            return True

    def update_portfolio(self, tick_event):
        """
        This updates all positions ensuring an up to date
        unrealised profit and loss (PnL).
        """
        self.time = datetime.utcfromtimestamp(tick_event.time)
        currency_pair = tick_event.instrument
        if currency_pair in self.positions:
            ps = self.positions[currency_pair]
            ps.update_position_price()
        if self.backtest:
            time = datetime.utcfromtimestamp(tick_event.time)
            out_line = "Time: %s, Balance: %0.2f," % (time.strftime('%Y-%m-%d %H:%M'), self.balance)
            for pair in self.ticker.pairs:
                if pair in self.positions:
                    out_line += "Position: %0.2f" % self.positions[pair].profit_base
                else:
                    out_line += ",0.00"
            out_line += "\n"
            self.logger.info(out_line[:-2])

    def execute_signal(self, signal_event):
        side = signal_event.side
        self.time = datetime.utcfromtimestamp(signal_event.time)
        currency_pair = signal_event.instrument

        if (signal_event.units == None):
            units = int(self.trade_units)
        else:
            units = int(signal_event.units * 0.001)
        # If there is no position, create one
        if currency_pair not in self.positions:
            if side == "true":
                position_type = "long"
            else:
                position_type = "short"
            self.add_new_position(position_type, currency_pair, units, self.time)
            self.trade_count += 1
        # If a position exists add or remove units
        else:
            ps = self.positions[currency_pair]
            if side == "true" and ps.position_type == "long":
                self.add_position_units(currency_pair, units)
            elif side == "false" and ps.position_type == "long":
                self.close_position(currency_pair)
            elif side == "true" and ps.position_type == "short":
                self.close_position(currency_pair)
            elif side == "false" and ps.position_type == "short":
                self.add_position_units(currency_pair, units)
            else:
                print('###############')
        order = OrderEvent(currency_pair, units, "AtMarket", side)
        self.events.put(order)

    def get_win_rate(self):
        rate = float(self.win_count) / float(self.trade_count)
        return rate * 100

    def get_loss_rate(self):
        rate = float(self.loss_count) / float(self.trade_count)
        return rate * 100

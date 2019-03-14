import copy
from datetime import datetime
from decimal import Decimal
from pyllist import dllist
import talib as ta
import numpy as np


class Event(object):
    pass


class TickEvent(Event):
    open = None
    high = None
    low = None
    close = None

    def __init__(self, instrument, time, bid, ask):
        self.type = 'TICK'
        self.instrument = instrument
        self.time = time
        self.bid = bid
        self.ask = ask

    def __str__(self):
        return "Type: %s, Instrument: %s, Time: %s, Bid: %s, Ask: %s" % (
            str(self.type), str(self.instrument),
            str(self.time), str(self.bid), str(self.ask)
        )


class SignalEvent(Event):
    def __init__(self, instrument, order_type, side, time):
        self.type = 'SIGNAL'
        self.instrument = instrument
        self.order_type = order_type
        self.side = side
        self.time = time
        self.units = None

    def __str__(self):
        return "Type: %s, Instrument: %s, Order Type: %s, Side: %s" % (
            str(self.type), str(self.instrument),
            str(self.order_type), str(self.side)
        )


class OrderEvent(Event):
    def __init__(self, instrument, units, order_type, side):
        self.type = 'ORDER'
        self.instrument = instrument
        self.units = units
        self.order_type = order_type
        self.side = side


class Strategy(object):
    pass


class TestRandomStrategy(Strategy):
    def __init__(self, instrument, events):
        self.instrument = instrument
        self.events = events
        self.ticks = 0
        self.invested = False

    def calculate_signals(self, event):
        if event.type == 'TICK':
            self.ticks += 1
            if self.ticks % 5 == 0:
                if self.invested == False:
                    signal = SignalEvent(event.instrument, "AtMarket", "true", event.time)
                    self.events.put(signal)
                    self.invested = True
                else:
                    signal = SignalEvent(event.instrument, "AtMarket", "false", event.time)
                    self.events.put(signal)
                    self.invested = False


class MovingAverageCrossStrategy(Strategy):
    def __init__(
            self, pairs, events,
            short_window=10, long_window=50
    ):
        self.pairs = pairs
        self.pairs_dict = self.create_pairs_dict()
        self.events = events
        self.short_window = short_window
        self.long_window = long_window

    def create_pairs_dict(self):
        attr_dict = {
            "ticks": 0,
            "invested": False,
            "short_sma": None,
            "long_sma": None
        }
        pairs_dict = {}
        for p in self.pairs:
            pairs_dict[p] = copy.deepcopy(attr_dict)
        return pairs_dict

    def calc_rolling_sma(self, sma_m_1, window, price):
        return ((sma_m_1 * (window - 1)) + price) / window

    def calculate_signals(self, event):
        if event.type == 'TICK':
            pair = event.instrument
            price = event.bid
            pd = self.pairs_dict[pair]
            if pd["ticks"] == 0:
                pd["short_sma"] = price
                pd["long_sma"] = price
            else:
                pd["short_sma"] = self.calc_rolling_sma(
                    pd["short_sma"], self.short_window, price
                )
                pd["long_sma"] = self.calc_rolling_sma(
                    pd["long_sma"], self.long_window, price
                )
            # Only start the strategy when we have created an accurate short window
            if pd["ticks"] > self.short_window:
                if pd["short_sma"] > pd["long_sma"] and not pd["invested"]:
                    signal = SignalEvent(pair, "AtMarket", "true", event.time)
                    self.events.put(signal)
                    pd["invested"] = True
                if pd["short_sma"] < pd["long_sma"] and pd["invested"]:
                    signal = SignalEvent(pair, "AtMarket", "false", event.time)
                    self.events.put(signal)
                    pd["invested"] = False
            pd["ticks"] += 1
            # print(str(pd["short_sma"]) + " & " + str(pd["long_sma"]))


class BollingerBandStrategy(Strategy):
    '''
    * Middle Band = 20-day simple moving average (SMA)
    * Upper Band = 20-day SMA + (20-day standard deviation of price x 2)
    * Lower Band = 20-day SMA - (20-day standard deviation of price x 2)
    '''

    def __init__(
            self, pairs, events,
            sma_window=20
    ):
        self.pairs = pairs
        self.pairs_dict = self.create_pairs_dict()
        self.events = events
        self.sma_window = sma_window
        self.list = dllist()

    def create_pairs_dict(self):
        attr_dict = {
            "ticks": 0,
            "invested_long": False,
            "invested_short": False,
            "lower_band": None,
            "middle_band": None,
            "upper_band": None
        }
        pairs_dict = {}
        for p in self.pairs:
            pairs_dict[p] = copy.deepcopy(attr_dict)
        return pairs_dict

    def calc_rolling_sma(self, sma_m_1, window, price):
        return ((sma_m_1 * (window - 1)) + price) / window

    def calc_rolling_st(self, list, average):
        st_dev = 0
        for price in list:
            result = price - average
            result = result * result
            st_dev = st_dev + result
        st_dev = st_dev / 20
        return st_dev

    def calculate_signals(self, event):
        if event.type == 'TICK':
            pair = event.instrument
            price = event.bid
            pd = self.pairs_dict[pair]
            if pd["ticks"] < self.sma_window:
                pd["middle_band"] = price
                pd["lower_band"] = price
                pd["upper_band"] = price
                self.list.appendleft(price)
            else:
                pd["middle_band"] = self.calc_rolling_sma(
                    pd["middle_band"], self.sma_window, price
                )
                self.list.popright()
                self.list.appendleft(price)
                st_dev = self.calc_rolling_st(self.list, pd["middle_band"])
                pd["upper_band"] = pd["middle_band"] + 20 * st_dev
                pd["lower_band"] = pd["middle_band"] - 20 * st_dev
            # Only start the strategy when we have created an accurate short window
            if pd["ticks"] > self.sma_window:
                if price >= pd["upper_band"] and not pd["invested_short"]:
                    signal = SignalEvent(pair, "AtMarket", "false", event.time)
                    self.events.put(signal)
                    pd["invested_short"] = True
                if price <= pd["lower_band"] and not pd["invested_long"]:
                    signal = SignalEvent(pair, "AtMarket", "true", event.time)
                    self.events.put(signal)
                    pd["invested_long"] = True
                if price <= pd["middle_band"] and pd["invested_short"]:
                    signal = SignalEvent(pair, "AtMarket", "true", event.time)
                    self.events.put(signal)
                    pd["invested_short"] = False
                if price >= pd["middle_band"] and pd["invested_long"]:
                    signal = SignalEvent(pair, "AtMarket", "false", event.time)
                    self.events.put(signal)
                    pd["invested_long"] = False
            # print(price)
            print(str(pd["lower_band"]) + "," + str(pd["middle_band"]) + "," + str(pd["upper_band"]))
            pd["ticks"] += 1


class DonchianChannelStrategy(Strategy):
    '''
    * Upper Band = 20-day high
    * Lower Band = 20-day low
    '''

    def __init__(
            self, pairs, events,
            sma_window=20
    ):
        self.pairs = pairs
        self.pairs_dict = self.create_pairs_dict()
        self.events = events
        self.sma_window = sma_window
        self.list = dllist()

    def create_pairs_dict(self):
        attr_dict = {
            "ticks": 0,
            "invested_long": False,
            "invested_short": False,
            "lower_band": None,
            "upper_band": None
        }
        pairs_dict = {}
        for p in self.pairs:
            pairs_dict[p] = copy.deepcopy(attr_dict)
        return pairs_dict

    def calc_rolling_sma(self, sma_m_1, window, price):
        return ((sma_m_1 * (window - 1)) + price) / window

    def calc_upper(self, list):
        high = 0
        for price in list:
            if price > high:
                high = price
        return high

    def calc_lower(self, list):
        low = 999999999
        for price in list:
            if price < low:
                low = price
        return low

    def calculate_signals(self, event):
        if event.type == 'TICK':
            pair = event.instrument
            price = event.bid
            pd = self.pairs_dict[pair]
            if pd["ticks"] < self.sma_window:
                pd["middle_band"] = price
                pd["lower_band"] = price
                pd["upper_band"] = price
                self.list.appendleft(price)
            else:
                pd["middle_band"] = self.calc_rolling_sma(
                    pd["middle_band"], self.sma_window, price
                )
                self.list.popright()
                self.list.appendleft(price)
                pd["upper_band"] = self.calc_upper(self.list)
                pd["lower_band"] = self.calc_lower(self.list)
            # Only start the strategy when we have created an accurate short window
            if pd["ticks"] > self.sma_window:
                if price >= pd["upper_band"] and not pd["invested_long"]:
                    signal = SignalEvent(pair, "AtMarket", "true", event.time)
                    self.events.put(signal)
                    pd["invested_long"] = True
                if price <= pd["lower_band"] and not pd["invested_short"]:
                    signal = SignalEvent(pair, "AtMarket", "false", event.time)
                    self.events.put(signal)
                    pd["invested_short"] = True
                if price < pd["upper_band"] and price > pd["lower_band"] and pd["invested_long"]:
                    signal = SignalEvent(pair, "AtMarket", "false", event.time)
                    self.events.put(signal)
                    pd["invested_long"] = False
                if price < pd["upper_band"] and price > pd["lower_band"] and pd["invested_short"]:
                    signal = SignalEvent(pair, "AtMarket", "true", event.time)
                    self.events.put(signal)
                    pd["invested_short"] = False
            # print(self.list)
            # print(price)
            print(str(pd["lower_band"]) + "," + str(pd["middle_band"]) + "," + str(pd["upper_band"]))
            pd["ticks"] += 1


class RSIStrategy(Strategy):
    time = None

    def __init__(
            self, pairs, events, window=14
    ):
        self.pairs = pairs
        self.pairs_dict = self.create_pairs_dict()
        self.events = events
        self.window = window
        self.list = dllist()

    def create_pairs_dict(self):
        attr_dict = {
            "ticks": 0,
            "invested_long": False,
            "invested_short": False,
            "rsi": None
        }
        pairs_dict = {}
        for p in self.pairs:
            pairs_dict[p] = copy.deepcopy(attr_dict)
        return pairs_dict

    def calc_rsi(self, list):
        avg_gain = 0
        avg_loss = 0
        prev_price = 0
        for price in list:
            if (prev_price == 0):
                prev_price = price
            if price - prev_price > 0:
                avg_gain = avg_gain + (price - prev_price)
            if price - prev_price < 0:
                avg_loss = avg_loss + (prev_price - price)
        avg_gain = Decimal(avg_gain / self.window)
        avg_loss = Decimal(avg_loss / self.window)
        # print('avg_gain=' + str(avg_gain) + ", avg_loss=" + str(avg_loss))
        if (avg_loss == 0):
            rs = 0
        else:
            rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_signals(self, event):

        if event.type == 'TICK':
            pair = event.instrument
            price = (event.high + event.low) / 2
            self.time = datetime.utcfromtimestamp(event.time)
            # print(event.time, event.ask, event.bid)

            pd = self.pairs_dict[pair]
            if pd["ticks"] < self.window + 10:
                pd["rsi"] = 50
                self.list.appendright(price)
            else:
                self.list.popleft()
                self.list.appendright(price)
                npa = np.asarray(self.list, dtype=np.float64)
                rsi14 = ta.RSI(npa, timeperiod=self.window)
                pd["rsi"] = rsi14[-1]

            # Only start the strategy when we have created an accurate short window
            if pd["ticks"] > self.window:
                if pd["rsi"] < 30 and not pd["invested_long"]:
                    signal = SignalEvent(pair, "AtMarket", "true", event.time)
                    self.events.put(signal)
                    pd["invested_long"] = True
                if pd["rsi"] > 70 and not pd["invested_short"]:
                    signal = SignalEvent(pair, "AtMarket", "false", event.time)
                    self.events.put(signal)
                    pd["invested_short"] = True
                if pd["rsi"] > 50 and pd["invested_long"]:
                    signal = SignalEvent(pair, "AtMarket", "false", event.time)
                    self.events.put(signal)
                    pd["invested_long"] = False
                if pd["rsi"] < 50 and pd["invested_short"]:
                    signal = SignalEvent(pair, "AtMarket", "true", event.time)
                    self.events.put(signal)
                    pd["invested_short"] = False
            # print(str(pd["rsi"]))
            pd["ticks"] += 1


class PortfolioAllocation(Strategy):
    def __init__(
            self, pairs, events, equity=1000000.0,
            pair_targets=[40]
    ):
        self.pairs = pairs
        self.pair_targets = pair_targets
        self.equity = equity
        self.pairs_dict = self.create_pairs_dict()
        self.events = events

    def create_pairs_dict(self):
        attr_dict = {
            "ticks": 0,
            "equity": self.equity,
            "target_percent": 0,
            "current_percent": 0,
            "pair_units": 0

        }
        pairs_dict = {}
        pair_index = 0;
        for p in self.pairs:
            pairs_dict[p] = copy.deepcopy(attr_dict)
            pairs_dict[p]["target_percent"] = self.pair_targets[pair_index]
            pair_index += 1
        return pairs_dict

    def calculate_signals(self, event):
        if event.type == 'TICK':
            pair = event.instrument
            ask_price = float(event.ask)
            bid_price = float(event.bid)
            pd = self.pairs_dict[pair]
            # print('2',pd["current_percent"])
            if pd["ticks"] < 1:
                signal = SignalEvent(pair, "AtMarket", "true", event.time)
                # below statement: 0.01 is for percentage, 0.001 is for buying amount
                signal.units = (self.equity / ask_price) * pd["target_percent"] * 0.01
                self.events.put(signal)
                pd["pair_units"] = signal.units
                pd["current_percent"] = (ask_price * pd["pair_units"]) / self.equity * 100
            else:
                pd["current_percent"] = (ask_price * pd["pair_units"]) / self.equity * 100
            if pd["ticks"] > 0:
                if abs(pd["target_percent"] - pd["current_percent"]) > 2:
                    if (pd["target_percent"] - pd["current_percent"]) > 0:
                        signal = SignalEvent(pair, "AtMarket", "true", event.time)
                        signal.units = (self.equity / ask_price) * (pd["target_percent"] - pd["current_percent"]) * 0.01
                        pd["pair_units"] += signal.units
                        pd["current_percent"] = (ask_price * pd["pair_units"]) / self.equity * 100
                        self.events.put(signal)
                    if (pd["target_percent"] - pd["current_percent"]) < 0:
                        signal = SignalEvent(pair, "AtMarket", "false", event.time)
                        signal.units = (self.equity / bid_price) * (pd["current_percent"] - pd["target_percent"]) * 0.01
                        pd["pair_units"] -= signal.units
                        pd["current_percent"] = (bid_price * pd["pair_units"]) / self.equity * 100
                        self.events.put(signal)
            pd["ticks"] += 1

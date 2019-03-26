import json
from datetime import datetime
from decimal import Decimal

from dateparser import parse

from broker.oanda.common.constants import OrderType


class SignalAction(object):
    OPEN = 'OPEN'
    CLOSE = 'CLOSE'
    UPDATE = 'UPDATE'


class MarketAction(object):
    OPEN = 'OPEN'
    CLOSE = 'CLOSE'


class EventType(object):
    DEBUG = 'DEBUG'
    STARTUP = 'STARTUP'
    SHUTDOWN = 'SHUTDOWN'
    HEARTBEAT = 'HEARTBEAT'
    TICK = 'TICK'
    TICK_PRICE = 'TICK_PRICE'
    TIMEFRAME = 'TIMEFRAME'
    SIGNAL = 'SIGNAL'
    ORDER_CLOSE = 'ORDER_CLOSE'
    ORDER_HOLDING = 'ORDER_HOLDING'
    TRADE_OPEN = 'TRADE_OPEN'
    TRADE_CLOSE = 'TRADE_CLOSE'
    ORDER = 'ORDER'
    MARKET_OPEN = 'MARKET_OPEN'
    MARKET_CLOSE = 'MARKET_CLOSE'


class Event(object):
    type = None

    def __init__(self):
        self.time = datetime.utcnow()

    def to_dict(self):
        data = self.__dict__.copy()
        for k in data.keys():
            if type(data[k]) in (str, float, int) or data[k] is None:
                pass
            elif type(data[k]) is Decimal:
                data[k] = float(data[k])
            elif isinstance(data[k], datetime):
                data[k] = 'datetime:%s' % data[k].strftime('%Y-%m-%d %H:%M:%S:%f')
            else:
                raise Exception('%s.%s is not serializable.' % (self.__class__.__name__, k))
        data['type'] = self.type
        return data

    @staticmethod
    def from_dict(data):
        instance = Event()
        for k in data.keys():
            if type(data[k]) is int or data[k] is None:
                pass
            elif type(data[k]) is float:
                data[k] = Decimal(str(data[k]))

            elif type(data[k]) is str:
                if data[k].startswith('datetime:'):
                    dt_str = data[k].replace('datetime:', '')
                    dt = parse(dt_str, date_formats=['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S:%f',
                                                     '%Y-%m-%dT%H:%M:%S'])
                    data[k] = dt or data[k]
            else:
                raise Exception('Event.from_dict %s=%s is not deserializable.' % (k, data[k]))
            setattr(instance, k, data[k])
        return instance


class StartUpEvent(Event):
    type = EventType.STARTUP


class HeartBeatEvent(Event):
    type = EventType.HEARTBEAT

    def __init__(self, hearbeat_count):
        super(HeartBeatEvent, self).__init__()
        self.counter = hearbeat_count


class DebugEvent(Event):
    type = EventType.DEBUG

    def __init__(self, action):
        super(DebugEvent, self).__init__()
        self.action = action


class TimeFrameEvent(Event):
    type = EventType.TIMEFRAME

    def __init__(self, timeframe, current_time, previous, timezone, time):
        super(TimeFrameEvent, self).__init__()
        self.timeframe = timeframe
        self.current_time = current_time
        self.previous = previous
        self.timezone = timezone
        self.time = time


class MarketEvent(Event):
    type = EventType.MARKET_OPEN

    def __init__(self, action):
        super(MarketEvent, self).__init__()
        self.action = action


class TickEvent(Event):
    type = EventType.TICK

    def __init__(self, instrument, time, bid, ask):
        self.instrument = instrument
        self.time = time
        self.bid = bid
        self.ask = ask
        super(TickEvent, self).__init__()

    def __str__(self):
        return "Type: %s, Instrument: %s, Time: %s, Bid: %s, Ask: %s" % (
            str(self.type), str(self.instrument),
            str(self.time), str(self.bid), str(self.ask)
        )


class TickPriceEvent(Event):
    type = EventType.TICK_PRICE

    def __init__(self, broker, instrument, time, bid, ask):
        self.broker = broker
        self.instrument = instrument
        self.time = time
        self.bid = bid
        self.ask = ask
        super(TickPriceEvent, self).__init__()

    def __str__(self):
        return "Type: %s, Instrument: %s, Time: %s, Bid: %s, Ask: %s" % (
            str(self.type), str(self.instrument),
            str(self.time), str(self.bid), str(self.ask)
        )


class SignalEvent(Event):
    type = EventType.SIGNAL

    def __init__(self, action, strategy_name, version, magic_number, instrument, side, order_type=OrderType.MARKET,
                 stop_loss=None,
                 take_profit=None, trailing_stop=None, percent=None, trade_id=None):
        self.action = action
        self.strategy = strategy_name
        self.version = version
        self.magic_number = magic_number
        self.instrument = instrument
        self.order_type = order_type
        self.side = side
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_stop = trailing_stop
        self.percent = percent
        self.trade_id = trade_id
        super(SignalEvent, self).__init__()

    def __str__(self):
        return "Type: %s, Instrument: %s, Order Type: %s, Side: %s" % (
            str(self.type), str(self.instrument),
            str(self.order_type), str(self.side)
        )


class OrderUpdateEvent(Event):
    """order update signal"""
    type = EventType.ORDER_CLOSE

    def __init__(self, strategy_name, version, magic_number, instrument, stop_loss=None, take_profit=None,
                 trailing_stop=None, percent=None):
        self.strategy = strategy_name
        self.version = version
        self.magic_number = magic_number
        self.instrument = instrument
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_stop = trailing_stop
        self.percent = percent
        super(OrderUpdateEvent, self).__init__()


class OrderHoldingEvent(Event):
    """order holding, to notify strategy to calculate close signal"""
    type = EventType.ORDER_HOLDING

    def __init__(self, magic_number, orders):
        self.orders = orders
        self.magic_number = magic_number
        super(OrderHoldingEvent, self).__init__()


class TradeCloseEvent(Event):
    type = EventType.ORDER_CLOSED

    def __init__(self, broker, account_id, order_id, instrument, lots, profit, pips, close_time, close_price):
        self.broker = broker
        self.account_id = account_id
        self.order_id = order_id
        self.instrument = instrument
        self.lots = lots
        self.profit = profit
        self.pips = pips
        self.close_time = close_time
        self.close_price = close_price
        super(TradeCloseEvent, self).__init__()


class TradeOpenEvent(Event):
    type = EventType.TRADE_OPEN

    def __init__(self, broker, account_id, trade_id, instrument, side, lots, open_time, open_price, stop_loss=None,
                 take_profit=None):
        self.broker = broker
        self.account_id = account_id
        self.trade_id = trade_id
        self.instrument = instrument
        self.side = side
        self.lots = lots
        self.open_time = open_time
        self.open_price = Decimal(str(open_price))
        self.stop_loss = Decimal(str(stop_loss)) if stop_loss else None
        self.take_profit = Decimal(str(take_profit)) if take_profit else None
        super(TradeOpenEvent, self).__init__()


class OrderEvent(Event):
    type = EventType.ORDER

    def __init__(self, instrument, units, order_type, side, expiry=None, price=None, lowerBound=None, upperBound=None,
                 stopLoss=None, takeProfit=None, trailingStop=None):
        self.instrument = instrument
        self.units = units
        self.order_type = order_type
        self.side = side
        self.expiry = expiry
        self.price = price
        self.lowerBound = lowerBound
        self.upperBound = upperBound
        self.stopLoss = stopLoss
        self.takeProfit = takeProfit
        self.trailingStop = trailingStop
        super(OrderEvent, self).__init__()

    def __str__(self):
        return "Type: %s, Instrument: %s, Units: %s, Order Type: %s, Side: %s" % (
            str(self.type), str(self.instrument), str(self.units),
            str(self.order_type), str(self.side)
        )


class ConnectEvent(Event):
    def __init__(self, action):
        self.action = action.upper()
        super(ConnectEvent, self).__init__()


class FillEvent(Event):
    """
    When an BaseExecutionHandler receives an OrderEvent it must transact the order. Once an order has been transacted it generates a FillEvent, which describes the cost of purchase or sale as well as the transaction costs, such as fees or slippage.
    The FillEvent is the Event with the greatest complexity. It contains a timestamp for when an order was filled, the symbol of the order and the exchange it was executed on, the quantity of shares transacted, the actual price of the purchase and the commission incurred.

    Encapsulates the notion of a Filled Order, as returned
    from a brokerage. Stores the quantity of an instrument
    actually filled and at what price. In addition, stores
    the commission of the trade from the brokerage.
    """

    def __init__(self, timeindex, symbol, exchange, quantity,
                 direction, fill_cost, commission=None):
        """
        Initialises the FillEvent object. Sets the symbol, exchange,
        quantity, direction, cost of fill and an optional
        commission.

        If commission is not provided, the Fill object will
        calculate it based on the trade size and Interactive
        Brokers fees.

        Parameters:
        timeindex - The bar-resolution when the order was filled.
        symbol - The instrument which was filled.
        exchange - The exchange where the order was filled.
        quantity - The filled quantity.
        direction - The direction of fill ('BUY' or 'SELL')
        fill_cost - The holdings value in dollars.
        commission - An optional commission sent from IB.
        """

        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost

        # Calculate commission
        if commission is None:
            self.commission = self.calculate_ib_commission()
        else:
            self.commission = commission

    def calculate_ib_commission(self):
        """
        Calculates the fees of trading based on an Interactive
        Brokers fee structure for API, in USD.

        This does not include exchange or ECN fees.

        Based on "US API Directed Orders":
        https://www.interactivebrokers.com/en/index.php?f=commission&p=stocks2
        """
        full_cost = 1.3
        if self.quantity <= 500:
            full_cost = max(1.3, 0.013 * self.quantity)
        else:  # Greater than 500
            full_cost = max(1.3, 0.008 * self.quantity)
        full_cost = min(full_cost, 0.5 / 100.0 * self.quantity * self.fill_cost)
        return full_cost

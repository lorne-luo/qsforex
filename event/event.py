from datetime import datetime


class EventType(object):
    STARTUP = 'STARTUP'
    SHUTDOWN = 'SHUTDOWN'
    HEARTBEAT = 'HEARTBEAT'
    TICK = 'TICK'
    TICK_PRICE = 'TICK_PRICE'
    TIMEFRAME = 'TIMEFRAME'
    SIGNAL = 'SIGNAL'
    ORDER = 'ORDER'
    CLOSE = 'CLOSE'
    MARKET_OPEN = 'MARKET_OPEN'
    MARKET_CLOSE = 'MARKET_CLOSE'


class Event(object):
    type = None

    def __init__(self):
        self.time = datetime.utcnow()


class HeartBeatEvent(Event):
    type = EventType.HEARTBEAT


class TimeFrameEvent(Event):
    type = EventType.TIMEFRAME

    def __init__(self, timeframe,current,previous,timezone,time):
        super(TimeFrameEvent, self).__init__()
        self.timeframe = timeframe
        self.current = current
        self.previous = previous
        self.timezone = timezone
        self.time = time


class MarketOpenEvent(Event):
    type = EventType.MARKET_OPEN
    open = True


class MarketCloseEvent(Event):
    type = EventType.MARKET_CLOSE
    open = False


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

    def __init__(self, strategy_name, version, magic_number, instrument, order_type, side,strength):
        self.strategy = strategy_name
        self.version = version
        self.magic_number = magic_number
        self.instrument = instrument
        self.order_type = order_type
        self.side = side
        self.strength = strength
        super(SignalEvent, self).__init__()

    def __str__(self):
        return "Type: %s, Instrument: %s, Order Type: %s, Side: %s" % (
            str(self.type), str(self.instrument),
            str(self.order_type), str(self.side)
        )


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


class FillEvent(Event):
    """
    When an ExecutionHandler receives an OrderEvent it must transact the order. Once an order has been transacted it generates a FillEvent, which describes the cost of purchase or sale as well as the transaction costs, such as fees or slippage.
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

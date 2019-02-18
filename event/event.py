class Event(object):
    type = None


class TickEvent(Event):
    type = 'TICK'

    def __init__(self, instrument, time, bid, ask):
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
    type = 'SIGNAL'

    def __init__(self, instrument, order_type, side, time):
        self.instrument = instrument
        self.order_type = order_type
        self.side = side
        self.time = time  # Time of the last tick that generated the signal

    def __str__(self):
        return "Type: %s, Instrument: %s, Order Type: %s, Side: %s" % (
            str(self.type), str(self.instrument),
            str(self.order_type), str(self.side)
        )


class OrderEvent(Event):
    type = 'ORDER'

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

    def __str__(self):
        return "Type: %s, Instrument: %s, Units: %s, Order Type: %s, Side: %s" % (
            str(self.type), str(self.instrument), str(self.units),
            str(self.order_type), str(self.side)
        )

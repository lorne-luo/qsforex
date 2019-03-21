from datetime import datetime

from event.event import TimeFrameEvent, OrderHoldingEvent
from event.handler import QueueBase, BaseHandler
from utils.market import is_market_open


class SignalAction(object):
    OPEN = 'OPEN'
    CLOSE = 'CLOSE'


class StrategyBase(BaseHandler, QueueBase):
    name = None
    version = None
    magic_number = None
    source = None
    queue = None

    weekdays = [0, 1, 2, 3, 4]  # Mon to Fri
    timeframes = []
    hours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]  # GMT hour

    pairs = []
    data_reader = None
    params = {}
    subscription = [TimeFrameEvent.type, OrderHoldingEvent.type]

    stop_loss = 100
    take_profit = None
    trailing_stop = None

    def __str__(self):
        return '%s v%s #%s' % (self.name, self.version, self.magic_number)

    def __init__(self, queue, reader, *args, **kwargs):
        super(StrategyBase, self).__init__(queue)
        self.data_reader = reader

    def signal(self):
        if not is_market_open():
            return
        for symbol in self.pairs:
            self.signal_pair(symbol)

    def signal_pair(self, symbol):
        raise NotImplementedError

    def can_open(self):
        if not is_market_open():
            return False

        now = datetime.utcnow()
        if now.weekday() not in self.weekdays:
            return False
        if now.hour not in self.weekdays:
            return False
        return True

    def process(self, event):
        if event.type == TimeFrameEvent.type and event.timeframe in self.timeframes:
            self.signal()
        elif event.type == OrderHoldingEvent.type:
            self.signal()

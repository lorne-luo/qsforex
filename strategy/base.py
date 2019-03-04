from datetime import datetime

from event.handler import QueueBase
from utils.market import is_market_open


class StrategyBase(QueueBase):
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

    def __str__(self):
        return '%s v%s #%s' % (self.name, self.version, self.magic_number)

    def __init__(self, reader, queue, *args, **kwargs):
        super(StrategyBase, self).__init__(queue)
        self.data_reader = reader

    def calculate_signals(self):
        raise NotImplementedError

    def can_open_trade(self):
        if not is_market_open():
            return False

        now = datetime.utcnow()
        if now.weekday() not in self.weekdays:
            return False
        if now.hour not in self.weekdays:
            return False
        return True

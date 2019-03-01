import copy
import logging
from datetime import datetime

from event.event import *
from mt4.constants import PERIOD_CHOICES, get_candle_time

logger = logging.getLogger(__name__)


class QueueBase(object):
    queue = None

    def __init__(self, queue):
        self.queue = queue

    def set_queue(self, queue):
        if not self.queue:
            self.queue = queue

    def put(self, event):
        if self.queue:
            self.queue.put(event)
        else:
            logger.error('Handler do not have queue')


class BaseHandler(QueueBase):
    subscription = []

    def process(self, event):
        raise NotImplementedError


class DebugHandler(BaseHandler):
    subscription = ['*']

    def process(self, event):
        print(event.__dict__)


class TickHandler(BaseHandler):
    def process(self, event):
        pass


class HeartBeatPrintHandler(BaseHandler):
    subscription = [HeartBeatEvent]

    def process(self, event):
        if self.DEBUG:
            print('HeartBeat: %s' % datetime.utcnow())


class TimeFrameTicker(BaseHandler):
    subscription = [HeartBeatEvent]
    candle_time = {}
    market_open = False
    HOLIDAY = [(1, 1)]

    def __init__(self, queue=None):
        super(TimeFrameTicker, self).__init__(queue)

        now = datetime.utcnow()
        for timeframe in PERIOD_CHOICES:
            self.candle_time[timeframe] = get_candle_time(now, timeframe)

    def get_market_open(self, now):
        # GBP/USD,20181207 20:59:58.156,1.27418,1.27426
        # GBP/USD,20181209 22:02:52.967,1.27017,1.27138
        if now.weekday() == 5:
            return False
        if now.weekday() == 4:
            return now.hour < 20
        if now.weekday() == 6:
            return now.hour > 22

        for date in self.HOLIDAY:
            if (now.day, now.month) == date:
                return now.hour < 20 or now.hour > 22
        return True

    def is_nfp(self):
        # is day of USA NFP
        pass

    def process(self, event):
        now = datetime.utcnow()
        for timeframe in PERIOD_CHOICES:
            new = get_candle_time(now, timeframe)
            if self.candle_time[timeframe] != new:
                self.put(TimeFrameEvent(timeframe))
                print(self.candle_time[timeframe], new)
                self.candle_time[timeframe] = new

        open = self.get_market_open(now)
        if self.market_open != open:
            if open:
                self.put(MarketOpenEvent())
            else:
                self.put(MarketCloseEvent())
            self.market_open = open

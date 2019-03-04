import copy
import logging
from datetime import datetime

from event.event import *
from mt4.constants import PERIOD_CHOICES, get_candle_time
from utils.market import is_market_open

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

    def __init__(self, queue=None):
        super(TimeFrameTicker, self).__init__(queue)

        now = datetime.utcnow()
        for timeframe in PERIOD_CHOICES:
            self.candle_time[timeframe] = get_candle_time(now, timeframe)

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

        open = is_market_open()
        if self.market_open != open:
            if open:
                self.put(MarketOpenEvent())
            else:
                self.put(MarketCloseEvent())
            self.market_open = open

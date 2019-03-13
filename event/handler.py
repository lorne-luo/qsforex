import copy
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

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

    def __init__(self, queue, events=None, *args, **kwargs):
        super(DebugHandler, self).__init__(queue)
        self.subscription = events or ['*']

    def process(self, event):
        print('[%s] %s' % (event.type, event.__dict__))


class EventLoggerHandler(DebugHandler):
    def __init__(self, queue, events=None, *args, **kwargs):
        super(EventLoggerHandler, self).__init__(queue, events, *args, **kwargs)
        self.logger = logging.getLogger('EventLog')

    def process(self, event):
        self.logger.info('[%s] %s' % (event.type, event.__dict__))


class TickHandler(BaseHandler):
    def process(self, event):
        pass


class HeartBeatPrintHandler(BaseHandler):
    subscription = [HeartBeatEvent]

    def process(self, event):
        if self.DEBUG:
            print('HeartBeat: %s' % datetime.utcnow())


class TimeFrameTicker(BaseHandler):
    subscription = [HeartBeatEvent, TickPriceEvent]
    candle_time = {}
    market_open = False
    timezone = 0

    def __init__(self, queue=None, timezone=0):
        super(TimeFrameTicker, self).__init__(queue)
        self.timezone = timezone
        self.market_open = is_market_open()
        now = self.get_now()
        for timeframe in PERIOD_CHOICES:
            self.candle_time[timeframe] = get_candle_time(now, timeframe)

    def is_nfp(self):
        # is day of USA NFP
        pass

    def get_now(self):
        now = datetime.utcnow() + relativedelta(hours=self.timezone)
        return now

    def process(self, event):
        if isinstance(event, TickPriceEvent):
            self.set_market_open(True)
        now = self.get_now()
        for timeframe in PERIOD_CHOICES:
            new = get_candle_time(now, timeframe)
            if self.candle_time[timeframe] != new:
                event = TimeFrameEvent(timeframe, new, self.candle_time[timeframe], self.timezone, now)
                self.put(event)
                # print(self.candle_time[timeframe], new)
                self.candle_time[timeframe] = new

        open = is_market_open()
        self.set_market_open(open)

    def set_market_open(self, open):
        if self.market_open != open:
            if open:
                self.put(MarketOpenEvent())
            else:
                self.put(MarketCloseEvent())
            self.market_open = open

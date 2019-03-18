import copy
import json
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

import settings
from event.event import *
from mt4.constants import PERIOD_CHOICES, get_candle_time, PERIOD_H1
from utils.market import is_market_open
from utils.redis import system_redis

logger = logging.getLogger(__name__)


class QueueBase(object):
    queue = None

    def __init__(self, queue):
        self.queue = queue

    def set_queue(self, queue):
        if not self.queue:
            self.queue = queue

    def put(self, event):
        try:
            data = json.dumps(event.to_dict())
            self.queue.put(data)
        except Exception as ex:
            logger.error('queue put error=%s' % ex)

    def get(self, block=False):
        try:
            data = self.queue.get(block)
            if data:
                data = json.loads(data)
                return Event.from_dict(data)
        except Exception as ex:
            logger.error('queue get error=%s' % ex)
        return None


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


class TickPriceHandler(BaseHandler):
    subscription = [TickPriceEvent.type]

    def process(self, event):
        key = "LAST_TICK_TIME"
        if settings.DEBUG:
            print(event.__dict__)
        else:
            system_redis.set(key, event.time.strftime('%Y-%m-%d %H:%M:%S:%f'))


class HeartBeatPrintHandler(BaseHandler):
    subscription = [HeartBeatEvent.type]

    def process(self, event):
        if self.DEBUG:
            print('HeartBeat: %s' % datetime.utcnow())


class TimeFrameTicker(BaseHandler):
    subscription = [HeartBeatEvent.type, TickPriceEvent.type]
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

                if timeframe == PERIOD_H1:
                    logger.info('H1 timeframe tick = %s' % new.strftime('%Y-%m-%d %H:%M'))

        open = is_market_open()
        self.set_market_open(open)

    def set_market_open(self, current_status):
        if self.market_open != current_status:
            if current_status:
                self.put(MarketEvent(MarketAction.OPEN))
                logger.info('Market status changed opened.')
            else:
                self.put(MarketEvent(MarketAction.CLOSE))
                logger.info('Market status changed closed.')
            self.market_open = current_status

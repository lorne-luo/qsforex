import logging
from queue import Empty

from dateutil.relativedelta import relativedelta

import settings
from event.event import *
from mt4.constants import PERIOD_CHOICES, get_candle_time, PERIOD_H1, get_mt4_symbol, PERIOD_D1
from utils.market import is_market_open
from utils.redis import system_redis, set_last_tick, get_last_tick, price_redis
from utils.telstra_api_v2 import send_to_admin

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
        except Empty:
            return None
        except Exception as ex:
            logger.error('queue get error=%s' % ex)
        return None


class BaseHandler(QueueBase):
    subscription = []
    account = None

    def __init__(self, queue, account=None, *args, **kwargs):
        super(BaseHandler, self).__init__(queue)
        self.account = account

    def process(self, event):
        raise NotImplementedError


class DebugHandler(BaseHandler):
    subscription = [DebugEvent.type]

    def __init__(self, queue, account=None, events=None, *args, **kwargs):
        super(DebugHandler, self).__init__(queue)
        self.subscription = events or []
        if DebugEvent.type not in self.subscription:
            self.subscription.append(DebugEvent.type)
        self.account = account

    def process(self, event):
        if event.type == DebugEvent.type and self.account:
            if event.action == 'account':
                self.account.log_account()
            elif event.action == 'trade':
                self.account.log_trade()
            elif event.action == 'order':
                self.account.log_order()
        else:
            print('[%s] %s' % (event.type, event.__dict__))


class EventLoggerHandler(DebugHandler):
    def __init__(self, queue, events=None, *args, **kwargs):
        super(EventLoggerHandler, self).__init__(queue, events, *args, **kwargs)

    def process(self, event):
        logger.info('[%s] %s' % (event.type, event.__dict__))


class TickPriceHandler(BaseHandler):
    subscription = [TickPriceEvent.type]

    def process(self, event):
        if settings.DEBUG:
            print(event.__dict__)
        else:
            set_last_tick(event.time.strftime('%Y-%m-%d %H:%M:%S:%f'))


class HeartBeatHandler(BaseHandler):
    subscription = [HeartBeatEvent.type]

    def process(self, event):
        if not event.counter % (settings.HEARTBEAT / settings.LOOP_SLEEP):
            if settings.DEBUG:
                print('HeartBeat: %s' % datetime.now())
            else:
                system_redis.set('HEARTBEAT', datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f'))

        if not event.counter % (120 * settings.HEARTBEAT / settings.LOOP_SLEEP):
            last_tick = get_last_tick()
            logger.info('[HeartBeatHandler] %s, last_tick=%s' % (event.time.strftime('%Y-%m-%d %H:%M:%S:%f'),
                                                                 last_tick))


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
            return
        else:
            open = is_market_open()
            self.set_market_open(open)

        now = self.get_now()
        for timeframe in PERIOD_CHOICES:
            new = get_candle_time(now, timeframe)
            if self.candle_time[timeframe] != new:
                event = TimeFrameEvent(timeframe, new, self.candle_time[timeframe], self.timezone, now)
                self.put(event)
                # print(self.candle_time[timeframe], new)
                self.candle_time[timeframe] = new

                if timeframe == PERIOD_H1:
                    last_tick = get_last_tick()
                    logger.info('TimeFrame H1 , market_open=%s, last_tick=%s' % (self.market_open, last_tick))

    def set_market_open(self, current_status):
        if self.market_open != current_status:
            if current_status:
                self.put(MarketEvent(MarketAction.OPEN))
                logger.info('[MarketEvent] Market opened.')
            else:
                self.put(MarketEvent(MarketAction.CLOSE))
                logger.info('[MarketEvent] Market closed.')
            self.market_open = current_status


pass


class PriceAlertHandler(BaseHandler):
    subscription = [TickPriceEvent.type, TimeFrameEvent.type, HeartBeatEvent.type]
    resistance_suffix = ['R1', 'R2', 'R3', 'R']
    support_suffix = ['S1', 'S2', 'S3', 'S']
    instruments = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'XAUUSD']
    prices = {}

    def __init__(self, queue, account=None, instruments=None, *args, **kwargs):
        super(PriceAlertHandler, self).__init__(queue)
        if instruments:
            self.instruments = [get_mt4_symbol(ins) for ins in instruments]
        self.update_price()

    def process(self, event):
        if event.type == TickPriceEvent.type:
            if event.instrument in self.instruments:
                self.price_alert(event)
        elif event.type == TimeFrameEvent.type:
            if event.timeframe == PERIOD_D1:
                self.reset_rs(event)
        elif event.type == HeartBeatEvent.type:
            if not event.counter % (settings.HEARTBEAT / settings.LOOP_SLEEP):
                self.update_price()

    def update_price(self):
        for ins in self.instruments:
            for suffix in self.resistance_suffix + self.support_suffix:
                key = '%s_%s' % (ins, suffix)
                self.prices[key] = price_redis.get(key)

    def price_alert(self, event):
        symbol = get_mt4_symbol(event.instrument)
        for resistance_level in self.resistance_suffix:
            key = '%s_%s' % (symbol, resistance_level)
            resistance = self.prices.get(key)
            if not resistance:
                continue

            price = Decimal(str(resistance))
            if event.bid > price:
                msg = '%s up corss %s = %s' % (symbol, resistance_level, price)
                logger.info('[PRICE_ALERT] %s' % msg)
                send_to_admin(msg)
                price_redis.delete(key)

        for support_level in self.support_suffix:
            key = '%s%s' % (symbol, support_level)
            support = self.prices.get(key)
            if not support:
                continue

            price = Decimal(str(support))
            if event.ask < price:
                msg = '%s down corss %s = %s' % (symbol, support_level, price)
                logger.info('[PRICE_ALERT] %s' % msg)
                send_to_admin(msg)
                price_redis.delete(key)

    def reset_rs(self, event):
        # todo reset resistance and support
        pass

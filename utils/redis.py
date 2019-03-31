import json
from datetime import datetime
from decimal import Decimal

import redis
import settings
from utils.time import str_to_datetime

LAST_TICK_TIME_KEY = 'LAST_TICK_TIME'
OPENING_TRADE_COUNT_KEY = 'OPENING_TRADE_COUNT'
TICK_PRICE_SUFFIX = '_LIST'

price_redis = redis.StrictRedis(host=settings.REDIS_HOST,
                                port=settings.REDIS_PORT,
                                db=settings.PRICE_CHANNEL,
                                decode_responses=True)

system_redis = redis.StrictRedis(host=settings.REDIS_HOST,
                                 port=settings.REDIS_PORT,
                                 db=settings.SYSTEM_CHANNEL,
                                 decode_responses=True)

order_redis = redis.StrictRedis(host=settings.REDIS_HOST,
                                port=settings.REDIS_PORT,
                                db=settings.SYSTEM_CHANNEL,
                                decode_responses=True)


def set_last_tick(dt):
    if isinstance(dt, datetime):
        dt = dt.strftime('%Y-%m-%d %H:%M:%S:%f')
    price_redis.set(LAST_TICK_TIME_KEY, dt)


def get_last_tick():
    return price_redis.get(LAST_TICK_TIME_KEY)


def get_tick_price(instrument):
    key = instrument.upper() + TICK_PRICE_SUFFIX
    data = price_redis.get(key)
    if data:
        price = json.loads(data)
        if 'ask' in price:
            price['ask'] = Decimal(str(price['ask']))
        if 'bid' in price:
            price['bid'] = Decimal(str(price['bid']))
        if 'time' in price:
            price['time'] = str_to_datetime(price['time'], format='%Y-%m-%d %H:%M:%S:%f')
        return price
    return None


def set_tick_price(instrument, data):
    key = instrument.upper() + TICK_PRICE_SUFFIX
    if not isinstance(data, str):
        data = json.dumps(data)
    price_redis.set(key, data)


class RedisQueue(object):
    """Simple Queue with Redis Backend"""

    def __init__(self, name, db=settings.SYSTEM_CHANNEL, host=settings.REDIS_HOST,
                 port=settings.REDIS_PORT):
        self.__db = redis.StrictRedis(host=host,
                                      port=port,
                                      db=db,
                                      decode_responses=True)
        self.key = 'queue:%s' % name

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        if item:
            self.__db.rpush(self.key, item)

    def get(self, block=False, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)

        if item:
            return item
        else:
            return None

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)

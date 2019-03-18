import json

import redis
import settings
from mt4.constants import get_mt4_symbol

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

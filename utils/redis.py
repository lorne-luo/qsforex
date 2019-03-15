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

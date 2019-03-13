import json

import redis
import settings
from mt4.constants import get_mt4_symbol

redis = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.DB_CHANNEL, decode_responses=True)



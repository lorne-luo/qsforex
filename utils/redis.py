import json

import redis
import settings

r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.DB_CHANNEL, decode_responses=True)


def tick_density(symbol, price):
    data = json.loads(r.get(symbol))
    data[price] = data[price] + 1 if data.get(price) else 1
    r.set(symbol, json.dumps(data))

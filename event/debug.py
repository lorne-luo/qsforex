import json

from event.event import DebugEvent
from utils.redis import RedisQueue


def debug(action, queue='FXCM'):
    event = DebugEvent(action)
    data = json.dumps(event.to_dict())
    queue = RedisQueue(queue)
    queue.put(data)

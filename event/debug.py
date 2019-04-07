import json

from event.event import DebugEvent, ConnectEvent
from utils.redis import RedisQueue


def debug(action, queue='FXCM'):
    """ action: order,trade,account"""
    event = DebugEvent(action)
    data = json.dumps(event.to_dict())
    queue = RedisQueue(queue)
    queue.put(data)


def connect_debug(action, queue='FXCM'):
    """action: connect,reconnect,disconnect, market_close, market_open"""
    queue = RedisQueue(queue)
    event = ConnectEvent(action)
    data = json.dumps(event.to_dict())
    queue.put(data)

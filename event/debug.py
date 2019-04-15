import json

from event.event import DebugEvent, ConnectEvent
from utils.redis import RedisQueue


def debug(action, queue='FXCM'):
    """ action: order, trade, account"""
    event = DebugEvent(action)
    data = json.dumps(event.to_dict())
    queue = RedisQueue(queue)
    queue.put(data)


def connect_debug(action, queue='FXCM'):
    """action: connect, reconnect, disconnect, status, market_close, market_open"""
    queue = RedisQueue(queue)
    event = ConnectEvent(action)
    data = json.dumps(event.to_dict())
    queue.put(data)


def order():
    debug('order')


def trade():
    debug('trade')


def account():
    debug('account')


def connect():
    connect_debug('connect')


def reconnect():
    connect_debug('reconnect')


def disconnect():
    connect_debug('disconnect')


def status():
    connect_debug('status')


def market_close():
    connect_debug('market_close')


def market_open():
    connect_debug('market_open')


def new_connect():
    connect_debug('new_connect')

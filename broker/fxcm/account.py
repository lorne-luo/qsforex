from collections import namedtuple
import requests
from socketIO_client import SocketIO
import logging
import json
import uuid
import threading
from dateutil.parser import parse
from datetime import datetime
import time
import types

from broker.base import BrokerAccount
from utils.singleton import SingletonDecorator
from utils.time import timestamp_to_str
from .config import FXCM_CONFIG



class FXCM(BrokerAccount):
    broker = 'FXCM'
    name = ''

    def __init__(self, bid=None, ask=None, high=None, low=None, updated=None,
                 symbol_info=None, parent=None):
        self.bid = bid
        self.ask = ask
        self.high = high
        self.low = low
        self.updated = updated
        self.output_fmt = "%r"
        self.parent = parent
        if symbol_info is not None:
            self.symbol_info = symbol_info
            self.offer_id = symbol_info['offerId']
            self.symbol = symbol_info['currency']
            precision = symbol_info['ratePrecision'] / 10.0
            self.output_fmt = "%s%0.1ff" % ("%", precision)
        super(FXCM, self).__init__()

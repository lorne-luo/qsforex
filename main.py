import logging
from queue import Queue

from fxcmpy import fxcmpy

import settings
from broker import SingletonFXCM
from broker.base import AccountType
from broker.fxcm.streaming import FXCMStreamRunner
from event.event import TickPriceEvent
from event.handler import DebugHandler, TimeFrameTicker, TimeFrameEvent, TickPriceHandler
from strategy.hlhb_trend import HLHBTrend
from utils.price_density import PriceDensityHandler
from utils.redis import RedisQueue

log_level = logging.INFO

logging.basicConfig(level=log_level,
                    format='%(asctime)s|%(levelname)s|%(threadName)s|%(name)s:%(lineno)d %(message)s')
logging.getLogger('FXCM').setLevel(logging.WARN)

price_queue = RedisQueue('Pricing')
# trade_queue = RedisQueue('Trading')
ACCESS_TOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'
ACCOUNT_ID = 3261139
pairs = ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'USD/CAD', 'AUD/USD', 'NZD/USD', 'XAU/USD']

fxcm = SingletonFXCM(AccountType.DEMO, ACCOUNT_ID, ACCESS_TOKEN)

timeframe_ticker = TimeFrameTicker(price_queue, 0)
price_density = PriceDensityHandler(price_queue, pairs)
hlhb_trend = HLHBTrend(price_queue, fxcm)

runner = FXCMStreamRunner(price_queue, pairs=pairs, access_token=ACCESS_TOKEN,
                          handlers=[timeframe_ticker, hlhb_trend, price_density])
runner.run()

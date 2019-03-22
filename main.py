import logging
from queue import Queue

from fxcmpy import fxcmpy

import settings
from broker import SingletonFXCM
from broker.base import AccountType
from broker.fxcm.streaming import FXCMStreamRunner
from event.event import TickPriceEvent
from event.handler import DebugHandler, TimeFrameTicker, TimeFrameEvent, TickPriceHandler
from execution.execution import BrokerExecutionHandler
from strategy.hlhb_trend import HLHBTrendStrategy
from utils.price_density import PriceDensityHandler
from utils.redis import RedisQueue

log_level = logging.INFO

logging.basicConfig(level=log_level,
                    format='%(asctime)s|%(levelname)s|%(threadName)s|%(name)s:%(lineno)d %(message)s')
logging.getLogger('FXCM').setLevel(logging.WARN)

queue = RedisQueue('FXCM')
# trade_queue = RedisQueue('Trading')
ACCESS_TOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'
ACCOUNT_ID = 3261139
pairs = ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'USD/CAD', 'AUD/USD', 'NZD/USD', 'XAU/USD']

fxcm = SingletonFXCM(AccountType.DEMO, ACCOUNT_ID, ACCESS_TOKEN)

timeframe_ticker = TimeFrameTicker(queue, timezone=0)
price_density = PriceDensityHandler(queue, fxcm, pairs)
hlhb_trend_strategy = HLHBTrendStrategy(queue, fxcm)
fxcm_execution = BrokerExecutionHandler(queue, fxcm)
debug = DebugHandler(queue, fxcm)

runner = FXCMStreamRunner(queue,
                          pairs=pairs,
                          api=fxcm.fxcmpy,
                          handlers=[timeframe_ticker, hlhb_trend_strategy, fxcm_execution, price_density, debug])
runner.run()

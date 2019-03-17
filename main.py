import logging
from queue import Queue

from broker.fxcm.streaming import FXCMStreamRunner
from event.event import TickPriceEvent
from event.handler import DebugHandler, TimeFrameTicker, TimeFrameEvent, TickPriceHandler
from utils.price_density import PriceDensityHandler

logging.FileHandler('/opt/qsforex/log/main.log')

queue = Queue()
YOURTOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'
pairs = ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'USD/CAD', 'AUD/USD', 'NZD/USD', 'XAU/USD']

tick_price_handler = TickPriceHandler(queue)
timeframe_ticker = TimeFrameTicker(queue, 0)
price_density = PriceDensityHandler(queue, pairs)

runner = FXCMStreamRunner(queue, pairs=pairs, access_token=YOURTOKEN,
                          handlers=[tick_price_handler, timeframe_ticker, price_density])
logging.info('%s started' % runner.__class__.__name__)
runner.run()

from queue import Queue

from broker.fxcm.streaming import FXCMStreamRunner
from event.handler import DebugHandler, TimeFrameTicker, TimeFrameEvent
from utils.price_density import PriceDensityHandler

queue = Queue()
YOURTOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'
pairs = ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'USD/CAD', 'AUD/USD', 'NZD/USD', 'XAU/USD']

debug = DebugHandler(queue, [TimeFrameEvent])
timeframe_ticker = TimeFrameTicker(queue, 0)
price_density = PriceDensityHandler(queue, pairs)

runner = FXCMStreamRunner(queue=queue, pairs=pairs, access_token=YOURTOKEN,
                          handlers=[debug, timeframe_ticker, price_density])
runner.run()

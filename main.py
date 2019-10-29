import logging
import settings
from broker import SingletonFXCM
from broker.base import AccountType
from broker.fxcm.streaming import FXCMStreamRunner
from event.event import TickPriceEvent
from event.handler import DebugHandler, TimeFrameTicker, TimeFrameEvent, TickPriceHandler, HeartBeatHandler, \
    PriceAlertHandler
from event.trade_manager import TradeManageHandler
from execution.execution import FXCMExecutionHandler
from strategy.hlhb_trend import HLHBTrendStrategy
from utils.price_density import PriceDensityHandler
from utils.redis import RedisQueue

log_level = logging.INFO

logging.basicConfig(level=log_level,
                    format='%(asctime)s|%(levelname)s|%(threadName)s|%(name)s:%(lineno)d %(message)s')
logging.getLogger('FXCM').setLevel(logging.WARN)

queue = RedisQueue('FXCM')
# trade_queue = RedisQueue('Trading')
pairs = ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'USD/CAD', 'AUD/USD', 'NZD/USD']

fxcm = SingletonFXCM(AccountType.DEMO, settings.FXCM_ACCOUNT_ID, settings.FXCM_ACCESS_TOKEN)

timeframe_ticker = TimeFrameTicker(queue, timezone=0)
heartbeat_handler = HeartBeatHandler(queue)
price_density = PriceDensityHandler(queue, fxcm, pairs)
hlhb_trend_strategy = HLHBTrendStrategy(queue, fxcm)
fxcm_execution = FXCMExecutionHandler(queue, fxcm)
trade_manage = TradeManageHandler(queue, fxcm)
debug = DebugHandler(queue, fxcm)
price_alert = PriceAlertHandler(None, instruments=pairs)

runner = FXCMStreamRunner(queue,
                          pairs=pairs,
                          api=fxcm.fxcmpy,
                          handlers=[timeframe_ticker, hlhb_trend_strategy, fxcm_execution, price_density, debug,
                                    heartbeat_handler, price_alert, trade_manage])
runner.run()

import json
import logging
from datetime import datetime
from decimal import Decimal
from queue import Empty

from fxcmpy import fxcmpy

from broker.base import AccountType
from broker.fxcm.constants import get_fxcm_symbol, ALL_SYMBOLS, FXCM_CONFIG
from event.event import TickPriceEvent, TimeFrameEvent
from event.runner import StreamRunnerBase
from mt4.constants import get_mt4_symbol
from utils.redis import price_redis

logger = logging.getLogger(__name__)


class FXCMStreamRunner(StreamRunnerBase):
    account = None
    broker = 'FXCM'
    max_prices = 4000

    def __init__(self, queue, *, pairs, access_token, handlers, account_type=AccountType.DEMO, **kwargs):
        super(FXCMStreamRunner, self).__init__(queue=queue, pairs=pairs)
        server = 'real' if account_type == AccountType.REAL else 'demo'
        self.account = fxcmpy(access_token=access_token, server=server)
        self.account.set_max_prices(self.max_prices)
        handlers = handlers or []
        self.register(*handlers)

    def run(self):
        logger.info('%s statup.' % self.__class__.__name__)
        logger.info('Registered handler: %s' % ', '.join([x.__class__.__name__ for x in self.handlers]))

        self.pairs = [get_fxcm_symbol(pair) for pair in self.pairs]
        pair_list = ",".join(self.pairs)
        logger.info('Pairs: %s\n' % pair_list)

        self.subscribe_pair()

    def subscribe_pair(self):
        # for symbol in ALL_SYMBOLS:
        #     if symbol not in self.pairs:
        #         self.account.unsubscribe_instrument(symbol)

        if not self.pairs:
            logger.info('No valid FXCM symbol exists.')
            return
        for pair in self.pairs:
            self.account.subscribe_market_data(pair, (self.tick_data,))
            self.account.subscribe_instrument(pair)

    def subscribe_data(self):
        # all_models['Offer', 'Account', 'Order', 'OpenPosition', 'ClosedPosition', 'Summary', 'Properties', 'LeverageProfile']
        models = ['Account', 'Order', 'OpenPosition', 'Summary']
        for model in models:
            self.account.subscribe_data_model(model, (self.model_event,))

    def unsubscribe_pair(self, pair):
        self.account.unsubscribe_market_data(pair)
        self.account.unsubscribe_instrument(pair)

    def unsubscribe_all(self):
        for pair in self.pairs:
            self.account.unsubscribe_market_data(pair)
            self.account.unsubscribe_instrument(pair)

        # ['Offer', 'Account', 'Order', 'OpenPosition', 'ClosedPosition', 'Summary', 'Properties', 'LeverageProfile']
        for model in self.account.models:
            self.account.unsubscribe_data_model(model)

    def model_event(self, data):
        # todo send event
        print(data)

    def tick_data(self, data, dataframe):
        instrument = get_mt4_symbol(data['Symbol'])
        time = datetime.fromtimestamp(int(data['Updated']) / 1000.0)

        bid = Decimal(str(data['Rates'][0]))
        ask = Decimal(str(data['Rates'][1]))
        tick = TickPriceEvent(self.broker, instrument, time, bid, ask)
        self.put(tick)
        price_redis.set('%s_TICK' % instrument.upper(),
                        json.dumps(
                            {'ask': float(ask), 'bid': float(bid), 'time': time.strftime('%Y-%m-%d %H:%M:%S:%f')}))

        while True:
            event = self.get(False)
            if event:
                self.handle_event(event)
            else:
                break

    def stop(self):
        self.account.close()
        super(FXCMStreamRunner, self).stop()


if __name__ == '__main__':
    from queue import Empty, Queue
    from event.handler import DebugHandler, TimeFrameTicker

    # from broker.fxcm.streaming import *
    queue = Queue()
    debug = DebugHandler(queue, events=[TimeFrameEvent])
    tft = TimeFrameTicker(queue, timezone=0)
    YOURTOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'
    pairs = ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'USD/CAD', 'AUD/USD', 'NZD/USD', 'XAU/USD',
             'USOil', 'USD/CNH']
    r = FXCMStreamRunner(queue, pairs=pairs, access_token=YOURTOKEN, handlers=[debug, tft])
    r.run()

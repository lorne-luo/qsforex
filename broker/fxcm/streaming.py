import logging
import time
from datetime import datetime
from decimal import Decimal
from queue import Empty

import fxcmpy
import pandas as pd

from broker.base import AccountType
from broker.fxcm.constants import get_fxcm_symbol, ALL_SYMBOLS, SingletonFXCMAPI, FXCM_CONFIG
from event.event import TickPriceEvent, TimeFrameEvent
from event.runner import StreamRunnerBase
from mt4.constants import get_mt4_symbol

logger = logging.getLogger(__name__)


class FXCMStreamRunner(StreamRunnerBase):
    connection = None
    broker = 'FXCM'
    MAX_PRICES = 4000

    def __init__(self, queue, pairs, access_token, handlers, account_type=AccountType.DEMO, *args, **kwargs):
        super(FXCMStreamRunner, self).__init__(queue=queue, pairs=pairs)
        server = 'real' if account_type == AccountType.REAL else 'demo'
        self.connection = SingletonFXCMAPI(access_token=access_token,
                                           server=server,
                                           log_level=FXCM_CONFIG.get('debugLevel', 'ERROR'),
                                           log_file=FXCM_CONFIG.get('logpath'))
        self.connection.set_max_prices(self.MAX_PRICES)
        handlers = handlers or []
        self.register(*handlers)

    def run(self):
        print('%s statup.' % self.__class__.__name__)
        print('Registered handler: %s' % ', '.join([x.__class__.__name__ for x in self.handlers]))

        self.pairs = [get_fxcm_symbol(pair) for pair in self.pairs]
        pair_list = ",".join(self.pairs)
        print('Pairs:', pair_list)
        print('\n')

        self.subscribe_pair()

    def subscribe_pair(self):
        for symbol in ALL_SYMBOLS:
            if symbol not in self.pairs:
                self.connection.unsubscribe_instrument(symbol)

        if not self.pairs:
            logger.info('No valid FXCM symbol exists.')
            return
        for pair in self.pairs:
            self.connection.subscribe_market_data(pair, (self.tick_data,))
            self.connection.subscribe_instrument(pair)

    def subscribe_data(self):
        # all_models['Offer', 'Account', 'Order', 'OpenPosition', 'ClosedPosition', 'Summary', 'Properties', 'LeverageProfile']
        models = ['Account', 'Order', 'OpenPosition', 'Summary']
        for model in models:
            self.connection.subscribe_data_model(model, (self.model_event,))

    def unsubscribe_pair(self, pair):
        self.connection.unsubscribe_market_data(pair)
        self.connection.unsubscribe_instrument(pair)

    def unsubscribe_all(self):
        for pair in self.pairs:
            self.connection.unsubscribe_market_data(pair)
            self.connection.unsubscribe_instrument(pair)

        # ['Offer', 'Account', 'Order', 'OpenPosition', 'ClosedPosition', 'Summary', 'Properties', 'LeverageProfile']
        for model in self.connection.models:
            self.connection.unsubscribe_data_model(model)

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

        try:
            event = self.queue.get(False)
        except Empty:
            pass
        else:
            if event:
                logger.debug("Received new %s event: %s", (event.type, event.__dict__))
                self.process_event(event)

    def stop(self):
        super(FXCMStreamRunner, self).stop()
        self.unsubscribe_all()
        self.connection.close()


if __name__ == '__main__':
    import queue
    from event.handler import DebugHandler, TimeFrameTicker

    # from broker.fxcm.streaming import *
    q = queue.Queue()
    debug = DebugHandler(q, [TimeFrameEvent])
    tft = TimeFrameTicker(q, 0)
    YOURTOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'
    pairs = ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'USD/CAD', 'AUD/USD', 'NZD/USD', 'XAU/USD',
             'USOil', 'USD/CNH']
    r = FXCMStreamRunner(q, pairs, YOURTOKEN, [debug, tft])
    r.run()

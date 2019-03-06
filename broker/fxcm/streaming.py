import logging
import time
from datetime import datetime
from decimal import Decimal
from queue import Empty

import fxcmpy
import pandas as pd

from broker.base import AccountType
from broker.fxcm.constants import get_fxcm_symbol
from event.event import TickPriceEvent
from event.runner import StreamRunnerBase
from mt4.constants import get_mt4_symbol

logger = logging.getLogger(__name__)


class FXCMStreamRunner(StreamRunnerBase):
    connection = None
    broker = 'FXCM'

    def __init__(self, queue, pairs, access_token, account_type=None, *args, **kwargs):
        super(FXCMStreamRunner, self).__init__(queue=queue, pairs=pairs)
        server = 'real' if account_type == AccountType.REAL else 'demo'
        self.connection = fxcmpy.fxcmpy(access_token=access_token,
                                        server=server,
                                        log_level=kwargs.get('log_level') or 'warn',
                                        log_file=kwargs.get('log_file') or '/tmp/fxcm.log')
        self.connection.set_max_prices(2000)
        self.register(*args)

    def run(self):
        print('%s statup.' % self.__class__.__name__)
        print('Registered handler: %s' % ', '.join([x.__class__.__name__ for x in self.handlers]))

        self.pairs = [get_fxcm_symbol(pair) for pair in self.pairs]
        pair_list = ",".join(self.pairs)
        print('Pairs:', pair_list)
        print('\n')

        if self.pairs:
            for pair in self.pairs:
                self.subscribe(pair)
        else:
            logger.info('No valid FXCM symbol exists.')

    def subscribe(self, pair):
        print('FXCM subscribe %s' % pair)
        self.connection.subscribe_market_data(pair, (self.tick_data,))

        #['Offer', 'Account', 'Order', 'OpenPosition', 'ClosedPosition', 'Summary', 'Properties', 'LeverageProfile']
        #self.connection.subscribe_data_model()
        #self.connection.subscribe_instrument

    def unsubscribe(self, pair):
        self.connection.unsubscribe_market_data(pair)

    def unsubscribe_all(self):
        for pair in self.pairs:
            self.connection.unsubscribe_market_data(pair)

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


if __name__ == '__main__':
    import queue
    from event.handler import DebugHandler
    # from broker.fxcm.streaming import *
    q = queue.Queue()
    debug = DebugHandler(q)
    YOURTOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'

    r = FXCMStreamRunner(q, ['EUR/USD', 'GBP/USD'], YOURTOKEN, AccountType.DEMO, debug)
    r.run()

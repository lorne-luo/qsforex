import logging
from decimal import Decimal
from queue import Empty, Queue
import dateparser
import v20

from broker.base import AccountType
from broker.oanda.account import SingletonOANDAAccount
from event.event import HeartBeatEvent, TickPriceEvent
from event.runner import StreamRunnerBase
from broker.oanda.common.convertor import get_symbol
import settings

logger = logging.getLogger(__name__)

class OandaV20StreamRunner(StreamRunnerBase):
    default_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'NZD_USD', 'USD_CNH', 'XAU_USD']
    broker = 'OANDA'

    def __init__(self, queue, pairs, access_token, account_id, handlers, account_type=AccountType.DEMO,*args, **kwargs):
        super(StreamRunnerBase, self).__init__(queue)
        self.pairs = pairs
        self.prices = self._set_up_prices_dict()
        self.access_token = access_token
        self.account_id = account_id
        handlers = handlers or []
        self.register(*handlers)
        self.account=SingletonOANDAAccount(type=account_type,
                               account_id=account_id,
                               access_token=access_token,
                               application_name=settings.APPLICATION_NAME)

    def run(self):
        print('%s statup.' % self.__class__.__name__)
        print('Registered handler: %s' % ', '.join([x.__class__.__name__ for x in self.handlers]))

        pairs_oanda = [get_symbol(p) for p in self.pairs]
        pair_list = ",".join(pairs_oanda)
        print('Pairs:', pair_list)
        print('\n')

        stream_api = self.account.stream_api

        response = stream_api.pricing.stream(
            self.account_id,
            instruments=pair_list,
            snapshot=True,
        )

        for msg_type, msg in response.parts():
            if msg_type == "pricing.PricingHeartbeat":
                self.put(HeartBeatEvent())
            elif msg_type == "pricing.ClientPrice" and msg.type == 'PRICE':
                instrument = msg.instrument
                time = dateparser.parse(msg.time)
                bid = Decimal(str(msg.bids[0].price))
                ask = Decimal(str(msg.asks[0].price))
                self.put(TickPriceEvent(self.broker, instrument, time, bid, ask))
            else:
                print('Unknow type:', msg_type, msg.__dict__)

            try:
                event = self.queue.get(False)
            except Empty:
                self.put(HeartBeatEvent())
            else:
                if event:
                    logger.debug("Received new %s event: %s", (event.type, event.__dict__))
                    self.process_event(event)


if __name__ == '__main__':
    from event.runner import *
    from event.handler import *
    import settings

    queue = Queue(maxsize=2000)
    debug = DebugHandler(queue)
    runner = OandaV20StreamRunner(queue, ['EUR_USD', 'GBP_USD'],
                                  settings.ACCESS_TOKEN,
                                  settings.ACCOUNT_ID,
                                  [debug],
                                  AccountType.DEMO)
    runner.run()

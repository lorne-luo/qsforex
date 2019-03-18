import logging
from decimal import Decimal
from queue import Empty, Queue
import dateparser

from broker.base import AccountType
from broker.oanda.account import SingletonOANDAAccount
from event.runner import StreamRunnerBase
from broker.oanda.common.convertor import get_symbol

logger = logging.getLogger(__name__)


class OandaV20StreamRunner(StreamRunnerBase):
    default_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'NZD_USD', 'USD_CNH', 'XAU_USD']
    broker = 'OANDA'

    def __init__(self, queue, *, pairs, access_token, account_id, handlers, account_type=AccountType.DEMO, **kwargs):
        super(StreamRunnerBase, self).__init__(queue)
        self.pairs = pairs
        self.prices = self._set_up_prices_dict()
        self.access_token = access_token
        self.account_id = account_id
        handlers = handlers or []
        self.register(*handlers)
        self.account = SingletonOANDAAccount(type=account_type,
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

            while True:
                event = self.get(False)
                if event:
                    self.handle_event(event)
                else:
                    break

            if not self.running:
                self.stop()

    def stop(self):
        del self.account.api
        del self.account.stream_api
        del self.account
        super(OandaV20StreamRunner, self).stop()


if __name__ == '__main__':
    from event.runner import *
    from event.handler import *
    import settings

    queue = Queue(maxsize=2000)
    debug = DebugHandler(queue)
    runner = OandaV20StreamRunner(queue,
                                  pairs=['EUR_USD', 'GBP_USD'],
                                  access_token=settings.ACCESS_TOKEN,
                                  account_id=settings.ACCOUNT_ID,
                                  handlers=[debug],
                                  account_type=AccountType.DEMO)
    runner.run()

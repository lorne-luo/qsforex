from __future__ import print_function

from datetime import datetime
from decimal import Decimal, getcontext, ROUND_HALF_DOWN
import logging
import json
from queue import Empty

import dateparser
import requests
import v20

from qsforex.event.event import TickEvent
from qsforex.pricing.price import PriceHandler

import settings
from event.event import HeartBeatEvent, TickPriceEvent
from broker.oanda.common.convertor import get_symbol
from event.runner import StreamRunnerBase
from settings import OANDA_ENVIRONMENTS

logger = logging.getLogger(__name__)


class StreamingForexPrices(PriceHandler):
    def __init__(
            self, domain, access_token,
            account_id, pairs, events_queue
    ):
        self.domain = domain
        self.access_token = access_token
        self.account_id = account_id
        self.events_queue = events_queue
        self.pairs = pairs
        self.prices = self._set_up_prices_dict()
        self.logger = logging.getLogger(__name__)

    def invert_prices(self, pair, bid, ask):
        """
        Simply inverts the prices for a particular currency pair.
        This will turn the bid/ask of "GBPUSD" into bid/ask for
        "USDGBP" and place them in the prices dictionary.
        """
        getcontext().rounding = ROUND_HALF_DOWN
        inv_pair = "%s%s" % (pair[3:], pair[:3])
        inv_bid = (Decimal("1.0") / bid).quantize(
            Decimal("0.00001")
        )
        inv_ask = (Decimal("1.0") / ask).quantize(
            Decimal("0.00001")
        )
        return inv_pair, inv_bid, inv_ask

    def connect_to_stream(self):
        pairs_oanda = ["%s_%s" % (p[:3], p[3:]) for p in self.pairs]
        pair_list = ",".join(pairs_oanda)

        print(pair_list)
        print(self.account_id)
        print(self.access_token)

        try:
            requests.packages.urllib3.disable_warnings()
            s = requests.Session()
            url = "https://" + self.domain + "/v3/accounts/" + self.account_id + '/pricing/stream'
            headers = {'Authorization': 'Bearer ' + self.access_token}
            params = {'instruments': pair_list, 'accountId': self.account_id}
            req = requests.Request('GET', url, headers=headers, params=params)
            pre = req.prepare()
            resp = s.send(pre, stream=True, verify=False)
            return resp
        except Exception as e:
            s.close()
            print("Caught exception when connecting to stream\n" + str(e))

    def stream_to_queue(self):
        response = self.connect_to_stream()
        if response.status_code != 200:
            return
        for line in response.iter_lines(1):
            if line:
                try:
                    dline = line.decode('utf-8')
                    msg = json.loads(dline)
                except Exception as e:
                    self.logger.error(
                        "Caught exception when converting message into json: %s" % str(e)
                    )
                    return
                if "instrument" in msg:
                    # self.logger.debug(msg)
                    getcontext().rounding = ROUND_HALF_DOWN
                    instrument = msg["instrument"].replace("_", "")
                    time = msg["time"]
                    bid = Decimal(str(msg["bids"][1]["price"])).quantize(
                        Decimal("0.00001")
                    )
                    ask = Decimal(str(msg["asks"][1]["price"])).quantize(
                        Decimal("0.00001")
                    )
                    self.prices[instrument]["bid"] = bid
                    self.prices[instrument]["ask"] = ask
                    # Invert the prices (GBP_USD -> USD_GBP)
                    inv_pair, inv_bid, inv_ask = self.invert_prices(instrument, bid, ask)
                    self.prices[inv_pair]["bid"] = inv_bid
                    self.prices[inv_pair]["ask"] = inv_ask
                    self.prices[inv_pair]["time"] = time
                    tev = TickEvent(instrument, time, bid, ask)
                    self.events_queue.put(tev)


class OandaV20StreamRunner(StreamRunnerBase):
    default_pairs = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'NZD_USD', 'USD_CNH', 'XAU_USD']

    def __init__(self, queue, pairs, domain, access_token, account_id, *args, **kwargs):
        super(StreamRunnerBase, self).__init__(queue)
        self.pairs = pairs
        self.prices = self._set_up_prices_dict()
        self.domain = domain
        self.access_token = access_token
        self.account_id = account_id
        self.register(*args)

    def run(self):
        print('%s statup.' % self.__class__.__name__)
        print('Registered handler: %s' % ', '.join([x.__class__.__name__ for x in self.handlers]))

        pairs_oanda = [get_symbol(p) for p in self.pairs]
        pair_list = ",".join(pairs_oanda)
        print('Pairs:', pair_list)
        print('\n')

        stream_api = v20.Context(
            hostname=OANDA_ENVIRONMENTS["streaming"][self.domain],
            application=settings.APPLICATION_NAME,
            token=self.access_token,
            datetime_format='RFC3339'
        )

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
                self.put(TickPriceEvent(instrument, time, bid, ask))
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


class BacktestRunner(StreamRunnerBase):
    def __init__(self, queue, pairs, csv, *args, **kwargs):
        super(BacktestRunner, self).__init__(queue)
        self.pairs = pairs
        self.register(*args)
        # todo backtest with csv


if __name__ == '__main__':
    from event.runner import *
    from event.handler import *
    import queue, settings

    q = queue.Queue(maxsize=2000)
    d = DebugHandler(q)
    r = OandaV20StreamRunner(q, ['EUR_USD', 'GBP_USD'], 'practice', settings.ACCESS_TOKEN, settings.ACCOUNT_ID, d)
    r.run()

import logging
from decimal import Decimal, ROUND_HALF_UP

import dateparser

from mt4.constants import pip
from broker.oanda.common.view import price_to_string, heartbeat_to_string
from broker.oanda.common.convertor import get_symbol, lots_to_units
import settings

logger = logging.getLogger(__name__)


class PriceMixin(object):
    _prices = {}

    def _process_price(self, price):
        instrument = price.instrument
        time = dateparser.parse(price.time)
        bid = Decimal(str(price.bids[0].price))
        ask = Decimal(str(price.asks[0].price))
        spread = pip(instrument,ask - bid)
        self._prices[instrument] = {'time': time, 'bid': bid, 'ask': ask, 'spread': spread}

    # list
    def list_prices(self, instruments=None, since=None, includeUnitsAvailable=True):
        instruments = instruments or self.default_pairs
        response = self.api.pricing.get(
            self.account_id,
            instruments=",".join(instruments),
            since=since,
            includeUnitsAvailable=includeUnitsAvailable
        )

        prices = response.get("prices", 200)
        for price in prices:
            if settings.DEBUG:
                print(price_to_string(price))
            self._process_price(price)

        return self._prices

    def get_price(self, instrument, type='mid'):
        instrument = get_symbol(instrument)
        if not self._prices:
            self.list_prices()

        if instrument not in self._prices:
            self.list_prices(instruments=[instrument])

        price = self._prices.get(instrument)
        if type == 'mid':
            return (price['bid'] + price['ask']) / 2
        elif type == 'bid':
            return price['bid']
        elif type == 'ask':
            return price['ask']

    def streaming(self, instruments=None, snapshot=True):
        instruments = instruments or self.default_pairs
        # print(",".join(instruments))
        # print(self.account_id)

        response = self.stream_api.pricing.stream(
            self.account_id,
            instruments=",".join(instruments),
            snapshot=snapshot,
        )

        for msg_type, msg in response.parts():
            if msg_type == "pricing.PricingHeartbeat" and settings.DEBUG:
                print(msg_type, heartbeat_to_string(msg))
            elif msg_type == "pricing.ClientPrice" and msg.type == 'PRICE':
                self._process_price(msg)
                print(price_to_string(msg))
            else:
                print('Unknow type:', msg_type, msg.__dict__)

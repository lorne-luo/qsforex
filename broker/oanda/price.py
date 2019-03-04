import logging
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd

import dateparser

from broker.base import PriceBase
from broker.oanda.base import OANDABase
from mt4.constants import pip
from broker.oanda.common.view import price_to_string, heartbeat_to_string
from broker.oanda.common.convertor import get_symbol, lots_to_units, get_timeframe_granularity
import settings

logger = logging.getLogger(__name__)


class PriceMixin(OANDABase, PriceBase):
    _prices = {}

    def _process_price(self, price):
        instrument = price.instrument
        time = dateparser.parse(price.time)
        bid = Decimal(str(price.bids[0].price))
        ask = Decimal(str(price.asks[0].price))
        spread = pip(instrument, ask - bid)
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

    def get_candle(self, instrument, granularity, count=50, fromTime=None, toTime=None, price_type='M', smooth=False):
        instrument = get_symbol(instrument)
        granularity = get_timeframe_granularity(granularity)
        if isinstance(fromTime, str):
            fromTime = dateparser.parse(fromTime).strftime('%Y-%m-%dT%H:%M:%S')
        if isinstance(toTime, str):
            fromTime = dateparser.parse(toTime).strftime('%Y-%m-%dT%H:%M:%S')

        response = self.api.instrument.candles(instrument, granularity=granularity, count=count, fromTime=fromTime,
                                               toTime=toTime, price=price_type, smooth=smooth)

        if response.status != 200:
            logger.error('[GET_Candle]', response, response.body)
            return []

        candles = response.get("candles", 200)

        price = 'mid'
        if price_type == 'B':
            price = 'bid'
        elif price_type == 'A':
            price = 'ask'

        data = [[candle.time.split(".")[0],
                 getattr(candle, price, None).o,
                 getattr(candle, price, None).h,
                 getattr(candle, price, None).l,
                 getattr(candle, price, None).c,
                 candle.volume]
                for candle in candles]

        df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        df.head()

        return df

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

import json
import logging
from decimal import Decimal

from broker.base import PriceBase
from broker.fxcm.constants import get_fxcm_symbol, get_fxcm_timeframe
from broker.oanda.base import OANDABase
from mt4.constants import get_mt4_symbol, pip
from utils.redis import price_redis, get_tick_price

logger = logging.getLogger(__name__)


class PriceMixin(OANDABase, PriceBase):
    _prices = {}

    # list
    def list_prices(self, instruments=None, since=None, includeUnitsAvailable=True):
        result = {}
        for pair in self.pairs:
            result[pair] = self.fxcmpy.get_last_price(pair)

        return result

    def get_price(self, instrument, type='mid'):
        instrument = get_mt4_symbol(instrument)
        pip_u = pip(instrument)
        price = get_tick_price(instrument)
        if not price:
            raise Exception('get_price, %s price is None' % instrument)
        if type == 'ask':
            return Decimal(str(price.get('ask'))).quantize(pip_u)
        elif type == 'bid':
            return Decimal(str(price.get('bid'))).quantize(pip_u)
        elif type == 'mid':
            price = (price.get('bid') + price.get('ask')) / 2
            return Decimal(str(price)).quantize(pip_u)

    # def get_price(self, instrument, type='mid'):
    #     instrument = get_fxcm_symbol(instrument)
    #     pip_u = pip(instrument)

    #     data = self.fxcmpy.get_last_price(instrument)
    #     if type == 'mid':
    #         price = (data['Ask'] + data['Bid']) / 2
    #         return Decimal(str(price)).quantize(pip_u)
    #     elif type == 'ask':
    #         return Decimal(str(data['Ask'])).quantize(pip_u)
    #     elif type == 'bid':
    #         return Decimal(str(data['Bid'])).quantize(pip_u)

    def get_candle(self, instrument, granularity, count=120, fromTime=None, toTime=None, price_type='M', smooth=False):
        instrument = get_fxcm_symbol(instrument)
        granularity = get_fxcm_timeframe(granularity)
        return self.fxcmpy.get_candles(instrument, period=granularity, number=count, start=fromTime, end=toTime)

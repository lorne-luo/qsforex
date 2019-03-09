import logging

from broker.base import PriceBase
from broker.fxcm.constants import get_fxcm_symbol, get_fxcm_timeframe
from broker.oanda.base import OANDABase

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
        instrument = get_fxcm_symbol(instrument)
        return self.fxcmpy.get_last_price(instrument)

    def get_candle(self, instrument, granularity, count=120, fromTime=None, toTime=None, price_type='M', smooth=False):
        instrument = get_fxcm_symbol(instrument)
        granularity = get_fxcm_timeframe(granularity)
        return self.fxcmpy.get_candles(instrument,period=granularity,number=count,start=fromTime,end=toTime)

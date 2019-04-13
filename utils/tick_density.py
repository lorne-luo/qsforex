import logging
import pandas as pd
from decimal import Decimal
from pandas import DataFrame

from mt4.constants import get_mt4_symbol, pip

logger = logging.getLogger(__name__)


class PriceDensity(object):
    density = None

    def __init__(self):
        self.density = pd.DataFrame([],
                                    columns=['price', 'count', 'volume'])
        self.density = self.density.set_index('price')

    def read(self, instrument, prices):
        instrument = get_mt4_symbol(instrument)
        if isinstance(prices, DataFrame):
            for i in range(len(prices)):
                tick = prices.iloc[i]
                price = Decimal(str(tick['Bid'])) + Decimal(str(tick['Ask']))
                price /= 2
                self.process_price(instrument, price)

    def process_price(self, instrument, price, volume=None):
        _pip = pip(instrument)
        price = Decimal(str(price)).quantize(_pip)
        volume = volume or 0
        if price in self.density.index:
            count = self.density.loc[1]['count']
            old_volume = self.density.loc[1]['volume']
            temp_df = pd.DataFrame({'count': [count + 1], 'volume': [old_volume + volume]}, index=[price])
            self.density.update(temp_df)
        else:
            temp_df = pd.DataFrame([[price, 1, volume]], columns=['price', 'count', 'volume'])
            temp_df = temp_df.set_index('price')
            self.density = pd.concat([self.density, temp_df])

import logging
import dateparser
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

from v20.transaction import StopLossDetails, ClientExtensions, TakeProfitDetails, TrailingStopLossDetails

from mt4.constants import OrderSide
from oanda_v20.base import api, EntityBase
from oanda_v20.common.logger import log_error
from oanda_v20.common.view import print_entity
from oanda_v20.common.convertor import get_symbol, lots_to_units, get_timeframe_granularity
from oanda_v20.common.constants import TransactionName, OrderType, OrderPositionFill, TimeInForce
import settings

logger = logging.getLogger(__name__)


class InstrumentMixin(EntityBase):
    @property
    def instruments(self):
        if self._instruments:
            return self._instruments
        else:
            return self.list_instruments()

    def list_instruments(self):
        """get all avaliable instruments"""
        response = self.api.account.instruments(self.account_id)
        instruments = response.get("instruments", "200")
        if not len(instruments):
            return

        # all_currencies=['name', 'type', 'displayName', 'pipLocation', 'displayPrecision', 'tradeUnitsPrecision', 'minimumTradeSize', 'maximumTrailingStopDistance', 'minimumTrailingStopDistance', 'maximumPositionSize', 'maximumOrderUnits', 'marginRate', 'commission']
        # columns = ['name', 'type', 'displayName', 'pipLocation', 'displayPrecision', 'marginRate']
        # all_currencies=[i.name for i in instruments]
        # currencies = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'NZD_USD', 'USD_CNH', 'XAU_USD']

        data = {}
        for i in instruments:
            if i.name in self.DEFAULT_CURRENCIES:
                data[i.name] = {'name': i.name,
                                'type': i.type,
                                'displayName': i.displayName,
                                'pipLocation': i.pipLocation,
                                'pip': 10 ** i.pipLocation,
                                'displayPrecision': i.displayPrecision,
                                'marginRateDisplay': "{:.0f}:1".format(1.0 / float(i.marginRate)),
                                'marginRate': i.marginRate, }

        self._instruments = data
        return self._instruments

    def get_pip_unit(self, instrument):
        """get pip unit for instrument"""
        instrument = get_symbol(instrument)
        try:
            unit = self.instruments[instrument].get('pip')
            return Decimal(str(unit))
        except KeyError:
            return None

    def get_pips(self, value, instrument):
        """calculate pip"""
        instrument = get_symbol(instrument)
        unit = self.get_pip_unit(instrument)
        value = Decimal(str(value))
        place_location = self.instruments[instrument]['displayPrecision'] + self.instruments[instrument]['pipLocation']
        places = 10 ** (place_location * -1)
        return (value / unit).quantize(Decimal(str(places)), rounding=ROUND_HALF_UP)

    def calculate_price(self, base_price, side, pip, instrument):
        instrument = get_symbol(instrument)
        pip_unit = self.get_pip_unit(instrument)
        base_price = Decimal(str(base_price))
        pip = Decimal(str(pip))

        if side == OrderSide.BUY:
            return base_price + pip * pip_unit
        elif side == OrderSide.SELL:
            return base_price - pip * pip_unit

    def get_candle(self, instrument, granularity, count=50, fromTime=None, toTime=None, price_type='M', smooth=False):
        instrument = get_symbol(instrument)
        granularity = get_timeframe_granularity(granularity)
        if isinstance(fromTime, str):
            fromTime = dateparser.parse(fromTime).strftime('%Y-%m-%dT%H:%M:%S')
        if isinstance(toTime, str):
            fromTime = dateparser.parse(toTime).strftime('%Y-%m-%dT%H:%M:%S')

        response = api.instrument.candles(instrument, granularity=granularity, count=count, fromTime=fromTime,
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

        df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'open', 'volume'])
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        df.head()

        return df

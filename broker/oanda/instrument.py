import logging
import dateparser
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP


from mt4.constants import OrderSide, pip
from broker.oanda.base import api, EntityBase
from broker.oanda.common.convertor import get_symbol, get_timeframe_granularity

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



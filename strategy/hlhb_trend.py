from datetime import datetime

from broker.oanda.common.constants import OrderType
from event.event import SignalEvent
from mt4.constants import PERIOD_H1
from strategy.base import StrategyBase
from strategy.helper import check_cross
from utils.market import is_market_open
import talib as ta
from talib import MA_Type


class HLHBTrend(StrategyBase):
    """
    Basically, I’m catching trends whenever the 5 EMA crosses above or below the 10 EMA.
    A trade is only valid if RSI crosses above or below the 50.00 mark when the signal pops up.
    And in this version, I’m adding ADX>25 to weed out the fakeouts.

    As for stops, I’ll continue to use a 150-pip trailing stop and a profit target of 400 pips.
    This might change in the future, but I’ll stick to this one for now.

    https://www.babypips.com/trading/forex-hlhb-system-20190128
    """
    name = 'HLHB Trend'
    version = '0.1'
    magic_number = '20190304'
    source = 'https://www.babypips.com/trading/forex-hlhb-system-20190128'

    weekdays = [0, 1, 2, 3, 4]
    timeframes = [PERIOD_H1]
    hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]  # GMT hour

    pairs = ['EURUSD']
    params = {'short_ema': 5,
              'long_ema': 10,
              'adx': 14, }

    def calculate_signals(self):
        if not is_market_open():
            return
        for symbol in self.pairs:
            self.process_pair(symbol)

    def process_pair(self, symbol):
        short_ema = self.params.get('short_ema')
        long_ema = self.params.get('long_ema')
        adx_period = self.params.get('adx')
        h1_candles = self.data_reader.get_candle(symbol, PERIOD_H1, count=50, fromTime=None, toTime=None,
                                                 price_type='M', smooth=False)
        adx = ta.ADX(h1_candles['high'], h1_candles['low'], h1_candles['close'], timeperiod=adx_period)
        if adx <= 25:
            return
        ema5 = ta.EMA(h1_candles['close'], timeperiod=short_ema)
        ema10 = ta.EMA(h1_candles['close'], timeperiod=long_ema)

        # upper, middle, lower = ta.BBANDS(h1_candles['close'], matype=MA_Type.T3)
        side = check_cross(ema5, ema10)
        if side:
            event = SignalEvent(self.name, self.version, self.magic_number,
                                symbol, OrderType.MARKET, side)
            self.put(event)

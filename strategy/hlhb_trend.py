import logging

import talib as ta

from broker.fxcm.constants import get_fxcm_symbol
from broker.oanda.common.constants import OrderType
from event.event import SignalEvent, SignalAction, TimeFrameEvent, OrderHoldingEvent, StartUpEvent
from mt4.constants import PERIOD_H1, OrderSide, PERIOD_M1
from strategy.base import StrategyBase
from strategy.helper import check_cross
from utils.market import is_market_open

logger = logging.getLogger(__name__)


class HLHBTrendStrategy(StrategyBase):
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

    timeframes = [PERIOD_H1]
    weekdays = [0, 1, 2, 3, 4]
    hours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]  # GMT hour

    subscription = [TimeFrameEvent.type, OrderHoldingEvent.type, StartUpEvent.type]

    pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD']
    params = {'short_ema': 5,
              'long_ema': 10,
              'adx': 14,
              'rsi': 14, }

    take_profit = 400
    trailing_stop = 150

    def signal_pair(self, symbol):
        short_ema = self.params.get('short_ema')
        long_ema = self.params.get('long_ema')
        adx_period = self.params.get('adx')
        rsi = self.params.get('rsi')

        candles = self.data_reader.get_candle(symbol, PERIOD_H1, count=50, fromTime=None, toTime=None,
                                              price_type='M', smooth=False)

        adx = ta.ADX(candles['askhigh'], candles['bidlow'], candles['bidclose'], timeperiod=adx_period)
        ema_short = ta.EMA(candles['bidclose'], timeperiod=short_ema)
        ema_long = ta.EMA(candles['bidclose'], timeperiod=long_ema)
        mean = (candles['askhigh'] + candles['bidlow']) / 2
        rsi = ta.RSI(mean, timeperiod=rsi)
        # upper, middle, lower = ta.BBANDS(h1_candles['close'], matype=MA_Type.T3)

        if self.can_open():
            self.open(symbol, ema_short, ema_long, adx, rsi)
        self.close(symbol, ema_short, ema_long, adx, rsi)

    def check_trade_exist(self, instrument, side):
        instrument = get_fxcm_symbol(instrument)
        is_buy = side == OrderSide.BUY
        for id, trade in self.account.get_trades():
            if trade.get_currency() == instrument and is_buy == trade.get_isBuy():
                return True
        return False

    def open(self, symbol, ema_short, ema_long, adx, rsi):
        logger.info('%s@%s param=%0.5f, %0.5f, %0.2f, %0.2f' % (
        self.name, symbol, ema_short[-1], ema_long[-1], adx[-1], rsi[-1]))

        if adx[-1] <= 25:
            return

        side = check_cross(ema_short, ema_long, shift=0)
        event = None
        if side == OrderSide.BUY and 70 > rsi[-1] > 50:
            event = SignalEvent(SignalAction.OPEN, self.name, self.version, self.magic_number,
                                symbol, OrderType.MARKET, side, trailing_stop=self.trailing_stop,
                                take_profit=self.take_profit)
            self.send_event(event)
        elif side == OrderSide.SELL and 50 > rsi[-1] > 30:
            event = SignalEvent(SignalAction.OPEN, self.name, self.version, self.magic_number,
                                symbol, OrderType.MARKET, side, trailing_stop=self.trailing_stop,
                                take_profit=self.take_profit)
            self.send_event(event)
        if event:
            logger.info('[ORDER_OPEN]%s|%s@%s %s, param=%0.5f, %0.5f, %0.2f, %0.2f' % (
                self.name, self.magic_number, symbol, side, ema_short[-1], ema_long[-1], adx[-1], rsi[-1]))

        return side

    def close(self, symbol, ema_short, ema_long, adx, rsi):
        pass

    def send_event(self, event):
        if event.action == SignalAction.OPEN:
            if self.check_trade_exist(event.instrument, event.side):
                logger.info('[ORDER_OPEN_SKIP] %s' % event.__dict__)
                return

        super(HLHBTrendStrategy, self).send_event(event)

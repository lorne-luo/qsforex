import logging
from oanda_v20.base import api, stream_api
import pandas as pd

from oanda_v20.common.convertor import get_symbol, get_timeframe_granularity

logger = logging.getLogger(__name__)


def get_candle(instrument, granularity, count=50, fromTime=None, toTime=None, price_type='M', smooth=False):
    instrument = get_symbol(instrument)
    granularity = get_timeframe_granularity(granularity)
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

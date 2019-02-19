from oanda_v20.api import api, stream_api


def get_candle(instrument, granularity, count=50, fromTime=None, toTime=None, price_type='M',smooth=False):
    response = api.instrument.candles(instrument, granularity=granularity, count=count, fromTime=fromTime,
                                      toTime=toTime, price=price_type,smooth=smooth)

    if response.status != 200:
        print(response)
        print(response.body)
        return []

    candles = response.get("candles", 200)

    if price_type == 'M':
        price = 'mid'
    elif price_type == 'B':
        price = 'bid'
    elif price_type == 'A':
        price = 'ask'

    data = [[candle.time.split(".")[0],
             getattr(candle, 'price', None).o,
             getattr(candle, 'price', None).h,
             getattr(candle, 'price', None).l,
             getattr(candle, 'price', None).c]
            for candle in response.get("candles", 200)]

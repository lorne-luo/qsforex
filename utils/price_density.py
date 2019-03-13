import json
import logging

import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_EVEN
import matplotlib.pyplot as plt
from dateparser import parse
from dateutil.relativedelta import relativedelta
from mt4.constants import PERIOD_D1, PERIOD_M5, PERIOD_M1
from broker.base import AccountType
from broker.fxcm.account import FXCM, SingletonFXCMAccount
from broker.fxcm.constants import get_fxcm_symbol
from event.event import TimeFrameEvent
from event.handler import BaseHandler
from mt4.constants import PIP_DICT, pip, get_mt4_symbol
from utils.redis import redis

ACCOUNT_ID = 3261139
ACCESS_TOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'

logger = logging.getLogger(__name__)


def _process_df(df, result, symbol):
    pip_unit = PIP_DICT[symbol]
    for index, row in df.iterrows():
        high = Decimal(str(row['askhigh'])).quantize(pip_unit, rounding=ROUND_HALF_EVEN)
        low = Decimal(str(row['bidlow'])).quantize(pip_unit, rounding=ROUND_HALF_EVEN)
        volume = Decimal(str(row['tickqty']))
        if not volume:
            continue
        distance = pip(symbol, high - low, True)
        avg_vol = (volume / distance).quantize(pip_unit)

        for i in range(int(distance) + 1):
            target = low + i * pip_unit
            if str(target) not in result:
                result[str(target)] = 0
            result[str(target)] = Decimal(str(result[str(target)])) + avg_vol


def _save_redis(symbol, result):
    output = ''
    keylist = result.keys()
    keys = sorted(keylist)
    for k in keys:
        output += '    %s: %s,\n' % (k, result[k])
    output = '''{
    %s
    }''' % output
    data = eval(output)
    redis.set(symbol, json.dumps(data))


def init_density(symbol, start=datetime(2019, 1, 18, 18, 1)):
    symbol = get_mt4_symbol(symbol)
    fxcm = SingletonFXCMAccount(AccountType.DEMO, ACCOUNT_ID, ACCESS_TOKEN)
    now = datetime.utcnow() - relativedelta(minutes=1)  # shift 1 minute
    end = datetime.utcnow()
    result = {}

    count = 0
    while end > start:
        df = fxcm.fxcmpy.get_candles(get_fxcm_symbol(symbol), period='m1', number=FXCM.MAX_CANDLES, end=end,
                                     columns=['askhigh', 'bidlow', 'tickqty'])
        _process_df(df, result, symbol)
        count += 1
        print(count, end)
        end = df.iloc[0].name.to_pydatetime() - relativedelta(seconds=30)

    _save_redis(symbol, result)
    redis.set(symbol + "_last_time", str(now))


def update_density(symbol, account=None):
    symbol = get_mt4_symbol(symbol)
    last_time = redis.get(symbol + "_last_time")
    last_time = parse(last_time) if last_time else None
    now = datetime.utcnow() - relativedelta(minutes=1)  # shift 1 minute
    data = redis.get(symbol)
    data = json.loads(data) if data else {}

    fxcm = account or SingletonFXCMAccount(AccountType.DEMO, ACCOUNT_ID, ACCESS_TOKEN)
    if last_time:
        df = fxcm.fxcmpy.get_candles(get_fxcm_symbol(symbol), period='m1', start=last_time, end=now,
                                     columns=['askhigh', 'bidlow', 'tickqty'])
    else:
        df = fxcm.fxcmpy.get_candles(get_fxcm_symbol(symbol), period='m1', number=FXCM.MAX_CANDLES, end=now,
                                     columns=['askhigh', 'bidlow', 'tickqty'])
    _process_df(df, data, symbol)

    print('Data length = %s' % len(df))
    _save_redis(symbol, data)
    redis.set(symbol + "_last_time", str(now))


def _draw(data, symbol, price, filename=None):
    symbol = get_mt4_symbol(symbol)
    pip_unit = PIP_DICT[symbol]
    fig = plt.figure()
    ax = plt.axes()
    items = data.items()
    y = [float(v) for k, v in items if pip(symbol, float(k) - price, True) < 100]
    x = [float(k) for k, v in items if pip(symbol, float(k) - price, True) < 100]
    ax.plot(x, y)
    plt.axvline(x=price, color='r')
    plt.xticks(np.arange(min(x), max(x), float(pip_unit * 10)), rotation=90)
    fig.show()
    if filename:
        fig.savefig('/tmp/%s.png' % filename)


def draw_history(symbol, price):
    price = float(price)
    symbol = get_mt4_symbol(symbol)
    data = redis.get(symbol)
    if not data:
        print('No data for %s' % symbol)
        return
    data = json.loads(data)
    filename = '%s_%s_history' % (symbol, datetime.utcnow().strftime('%Y-%m-%d %H:%M'))
    _draw(data, symbol, price, filename)


def draw_rencent(symbol, days=None):
    symbol = get_mt4_symbol(symbol)
    now = datetime.utcnow()

    fxcm = SingletonFXCMAccount(AccountType.DEMO, ACCOUNT_ID, ACCESS_TOKEN)
    df = fxcm.fxcmpy.get_candles(get_fxcm_symbol(symbol), period='m1', number=FXCM.MAX_CANDLES, end=now,
                                 columns=['askclose', 'askhigh', 'bidlow', 'tickqty'])
    price = df.iloc[-1].askclose
    if days:
        start = now - relativedelta(days=days)
        end = df.iloc[0].name.to_pydatetime() - relativedelta(seconds=30)
        print(end)
        while end - start > timedelta(minutes=1):
            if (end - start).days > 6:
                df2 = fxcm.fxcmpy.get_candles(get_fxcm_symbol(symbol), period='m1', number=FXCM.MAX_CANDLES, end=end,
                                              columns=['askclose', 'askhigh', 'bidlow', 'tickqty'])
            else:
                df2 = fxcm.fxcmpy.get_candles(get_fxcm_symbol(symbol), period='m1', start=start, end=end,
                                              columns=['askclose', 'askhigh', 'bidlow', 'tickqty'])
            df = df.append(df2, sort=True)
            end = df2.iloc[0].name.to_pydatetime() - relativedelta(seconds=30)
            print(end)

    result = {}
    _process_df(df, result, symbol)

    keylist = result.keys()
    keys = sorted(keylist)
    output = ''
    for k in keys:
        output += '    %s: %s,\n' % (k, result[k])
    output = '''{
        %s
        }''' % output
    sorted_result = eval(output)

    filename = '%s_%s' % (symbol, now.strftime('%Y-%m-%d %H:%M'))
    _draw(sorted_result, symbol, price, filename)


class PriceDensityHandler(BaseHandler):
    subscription = [TimeFrameEvent.type]
    pairs = []

    def __init__(self, queue=None, pairs=None):
        super(PriceDensityHandler, self).__init__(queue)
        self.pairs = pairs

    def process(self, event):
        if event.timeframe != PERIOD_M1:
            return

        for symbol in self.pairs:
            try:
                update_density(symbol)
                print('update_density succeed')
            except Exception as ex:
                logger.error('update_density error, symbol=%s, %s' % (symbol, ex))
                print('update_density error: %s'%ex)
                import traceback
                traceback.print_stack()

if __name__ == '__main__':
    #from utils.price_density import *
    update_density('EURUSD')
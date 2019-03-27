import json
import logging
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_EVEN
import matplotlib.pyplot as plt
from dateparser import parse
from dateutil.relativedelta import relativedelta

import settings
from mt4.constants import PERIOD_D1, PERIOD_M5, PERIOD_M1, PERIOD_H4
from broker.base import AccountType
from broker import FXCM, SingletonFXCM
from broker.fxcm.constants import get_fxcm_symbol
from event.event import TimeFrameEvent
from event.handler import BaseHandler
from mt4.constants import pip, get_mt4_symbol
from mt4.constants import pip_unit as get_pip_unit
from utils.redis import price_redis

TIME_SUFFIX = '_LAST_TIME'

logger = logging.getLogger(__name__)


def _process_df(df, result, symbol):
    pip_unit = get_pip_unit(symbol)
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
    price_redis.set('%s_H1' % symbol, json.dumps(data))


def init_density(symbol, start=datetime(2019, 1, 18, 18, 1), account=None):
    symbol = get_mt4_symbol(symbol)
    fxcm = account or SingletonFXCM(AccountType.DEMO, settings.FXCM_ACCOUNT_ID, settings.FXCM_ACCESS_TOKEN)
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
    price_redis.set(symbol + TIME_SUFFIX, str(now))


def update_density(symbol, account=None):
    symbol = get_mt4_symbol(symbol)
    last_time = price_redis.get(symbol + TIME_SUFFIX)
    last_time = parse(last_time) if last_time else None
    now = datetime.utcnow()
    data = price_redis.get('%s_H1' % symbol)
    data = json.loads(data) if data else {}

    fxcm = account or SingletonFXCM(AccountType.DEMO, ACCOUNT_ID, ACCESS_TOKEN)
    if last_time:
        df = fxcm.fxcmpy.get_candles(get_fxcm_symbol(symbol), period='m1', start=last_time, end=now,
                                     columns=['askhigh', 'bidlow', 'tickqty'])
    else:
        df = fxcm.fxcmpy.get_candles(get_fxcm_symbol(symbol), period='m1', number=FXCM.MAX_CANDLES, end=now,
                                     columns=['askhigh', 'bidlow', 'tickqty'])
    _process_df(df, data, symbol)

    print('Data length = %s' % len(df))
    _save_redis(symbol, data)
    now = df.iloc[-1].name.to_pydatetime() + relativedelta(seconds=30)
    price_redis.set(symbol + TIME_SUFFIX, str(now))
    return now


def _draw(data, symbol, price, filename=None, to_plotly=False):
    symbol = get_mt4_symbol(symbol)
    pip_unit = get_pip_unit(symbol)
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

    if to_plotly:
        trace = go.Bar(x=x, y=y)
        result = py.iplot([trace], filename=filename)
        print(result.embed_code)


def draw_history(symbol, price):
    price = float(price)
    symbol = get_mt4_symbol(symbol)
    data = price_redis.get('%s_H1' % symbol)
    if not data:
        print('No data for %s' % symbol)
        return
    data = json.loads(data)
    filename = '%s_%s_history' % (symbol, datetime.utcnow().strftime('%Y-%m-%d %H:%M'))
    _draw(data, symbol, price, filename)


def draw_recent(symbol, days=30, account=None, to_plotly=False):
    symbol = get_mt4_symbol(symbol)
    now = datetime.utcnow()

    fxcm = account or SingletonFXCM(AccountType.DEMO, settings.FXCM_ACCOUNT_ID, settings.FXCM_ACCESS_TOKEN)
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

    filename = '%s_%s days' % (symbol, days)
    _draw(sorted_result, symbol, price, filename, to_plotly)


def price_density_one_month(symbol, account=None, to_plotly=False):
    draw_recent(symbol, 30, account, to_plotly)


class PriceDensityHandler(BaseHandler):
    subscription = [TimeFrameEvent.type]
    pairs = []

    def __init__(self, queue=None, account=None, pairs=None):
        super(PriceDensityHandler, self).__init__(queue)
        self.pairs = pairs
        self.account = account

    def process(self, event):
        if event.timeframe != PERIOD_D1:
            return

        for symbol in self.pairs:
            try:
                last_time = update_density(symbol, self.account)
                logger.info('%s density updated to %s.' % (symbol, last_time.strftime('%Y-%m-%d %H:%M')))
            except Exception as ex:
                logger.error('update_density error, symbol=%s, %s' % (symbol, ex))


if __name__ == '__main__':
    # from utils.price_density import *
    update_density('EURUSD')
    draw_rencent('EURUSD')

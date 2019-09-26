from django.db import models
from django.utils.translation import ugettext_lazy as _


class Trade(models.Model):
    broker = models.CharField(_('broker'), max_length=12, blank=True)
    account_id = models.CharField(_('account_id'), max_length=12, blank=True)
    trade_id = models.CharField(_('trade_id'), max_length=12, blank=False)
    instrument = models.CharField(_('instrument'), max_length=12, blank=False)
    strategy_name = models.CharField(_('strategy_name'), max_length=12, blank=True)
    strategy_version = models.CharField(_('strategy_version'), max_length=12, blank=True)
    strategy_magic_number = models.IntegerField(_('strategy_magic_number'), blank=True, null=True)

    open_time = models.DateTimeField(_('open time'), auto_now_add=False, editable=True, blank=True, null=True)
    close_time = models.DateTimeField(_('close time'), auto_now_add=False, editable=True, blank=True, null=True)
    profitable_time = models.DecimalField(_('profitable time'), max_digits=8, decimal_places=2,blank=True, null=True)

    open_price = models.DecimalField(_('open_price'), max_digits=8, decimal_places=5,blank=True, null=True)
    close_price = models.DecimalField(_('close_price'), max_digits=8, decimal_places=5,blank=True, null=True)
    lots = models.DecimalField(_('lots'), max_digits=8, decimal_places=2,blank=True, null=True)
    pips = models.DecimalField(_('pips'), max_digits=8, decimal_places=2,blank=True, null=True)
    profit = models.DecimalField(_('profit'), max_digits=8, decimal_places=2,blank=True, null=True)

    max_profit = models.DecimalField(_('max_profit'), max_digits=8, decimal_places=2,blank=True, null=True)
    min_profit = models.DecimalField(_('min_profit'), max_digits=8, decimal_places=2,blank=True, null=True)
    drawdown = models.DecimalField(_('min_profit'), max_digits=8, decimal_places=5,blank=True, null=True)
    risk = models.DecimalField(_('risk'), max_digits=8, decimal_places=2,blank=True, null=True)


# time,microsecond,       order_id, symbol,  max, min,  current,last_profit,profit_seconds,profitable_time,last_tick
# 2019-04-10 09:07:56,801,207457615, NZDUSD, 0.0, -9.8, -9.0,    None,      0,             0.0,            2019-04-09 23:07:27.694000
from decimal import Decimal
from datetime import datetime
from django_orm.trade.models import *
path='/Users/lorne.luo/Workspace/lorne/qsforex/log/monitor.csv'
df =pd.read_csv(path)
account_id = '3266617'

for i in range(len(df)):
    trade_id = str(df.iloc[i]['order_id']).strip()
    trade = Trade.objects.filter(trade_id=trade_id).first()
    if not trade:
        open_time = datetime.strptime(df.iloc[i]['time'].strip(), '%Y-%m-%d %H:%M:%S')
        trade = Trade(open_time=open_time, account_id=account_id, trade_id=trade_id,
                      instrument=df.iloc[i]['symbol'],min_profit=0,max_profit=0,
                      strategy_name='HLHB Trend',
                      strategy_version='0.1',
                      strategy_magic_number='20190304'
                      )
    min_profit = Decimal(str(df.iloc[i]['min']).strip())
    max_profit = Decimal(str(df.iloc[i]['max']).strip())
    if min_profit < trade.min_profit:
        trade.min_profit = min_profit
    if max_profit > trade.max_profit:
        trade.max_profit = max_profit

    trade.profit=Decimal(str(df.iloc[i]['current']).strip())
    close_time = datetime.strptime(df.iloc[i]['last_tick'].strip(), '%Y-%m-%d %H:%M:%S.%f') if '.' in df.iloc[i]['last_tick'] else datetime.strptime(df.iloc[i]['last_tick'].strip(), '%Y-%m-%d %H:%M:%S')
    trade.close_time=close_time
    trade.profitable_time=Decimal(str(df.iloc[i]['profitable_time']))
    trade.save()
    print(i)
    pprint(trade.__dict__)
    break

import json
import logging
from datetime import datetime
from decimal import Decimal

import settings
from django_orm import Trade
from event.event import TickPriceEvent, TradeOpenEvent, TradeCloseEvent, HeartBeatEvent, MarketEvent
from event.handler import BaseHandler
from mt4.constants import profit_pip, OrderSide, get_mt4_symbol
from utils import telegram as tg
from utils.redis import system_redis, OPENING_TRADE_COUNT_KEY
from utils.time import datetime_to_str, str_to_datetime

logger = logging.getLogger(__name__)
TRADES_KEY = 'TRADES'


class TradeManageHandler(BaseHandler):
    subscription = [TickPriceEvent.type,
                    TradeOpenEvent.type,
                    TradeCloseEvent.type,
                    MarketEvent.type,
                    HeartBeatEvent.type]
    trades = {}

    def __init__(self, queue, account=None, *args, **kwargs):
        super(TradeManageHandler, self).__init__(queue, account)
        self.load_trades()

    def process(self, event):
        if event.type == TickPriceEvent.type:
            self.process_price(event)
        elif event.type == TradeOpenEvent.type:
            self.trade_open(event)
        elif event.type == TradeCloseEvent.type:
            self.trade_close(event)
        elif event.type == HeartBeatEvent.type:
            self.heartbeat(event)
        elif event.type == MarketEvent.type:
            self.load_trades()

    def get_trade(self, trade_id):
        trade_id = str(trade_id)
        return self.trades.get(trade_id)

    def pop_trade(self, trade_id):
        trade_id = str(trade_id)
        return self.trades.pop(trade_id, None)

    def process_price(self, event):
        for trade_id, trade in self.trades.items():
            if trade.get('instrument') == event.instrument:
                self.process_trade(trade, event)

    def process_trade(self, trade, event):
        price = event.bid if trade['side'] == OrderSide.BUY else event.ask
        profit_pips = profit_pip(event.instrument, trade.get('open_price'), price, trade.get('side'))
        trade['current'] = profit_pips
        if profit_pips > trade['max']:
            trade['max'] = profit_pips
        if profit_pips < trade['min']:
            trade['min'] = profit_pips

        if profit_pips >= 0:
            if not trade['last_profitable_start']:
                trade['last_profitable_start'] = datetime.utcnow()
        else:
            if trade['last_profitable_start']:
                self.update_profitable_seconds(trade)

        trade['last_tick_time'] = event.time

    def trade_open(self, event):
        trade_id = str(event.trade_id)
        if trade_id not in self.trades:
            trade = event.to_dict().copy()
            trade['broker'] = event.broker
            trade['account_id'] = event.account_id
            trade['trade_id'] = event.trade_id
            trade['instrument'] = event.instrument
            trade['side'] = event.side
            trade['lots'] = event.lots
            trade['open_time'] = event.open_time
            trade['open_price'] = event.open_price
            trade['magic_number'] = event.magic_number
            trade['max'] = 0
            trade['min'] = 0
            trade['current'] = 0
            trade['profitable_seconds'] = 0
            trade['last_profitable_start'] = None
            trade['last_tick_time'] = None

            self.trades[trade_id] = trade

        system_redis.set(OPENING_TRADE_COUNT_KEY, len(self.trades))

    def trade_close(self, event):
        trade = self.get_trade(event.trade_id)
        if not trade:
            logger.error('[Trade_Manage] Trade closed with no data in trade manager.')
            return
        # entry accuracy= 1 - min / (max-min)
        # exit accuracy= 1 - profit missed / (max-min)
        # risk:reward= 1: max/-min or 1:max

        if trade['last_profitable_start']:
            self.update_profitable_seconds(trade)

        close_time = event.close_time
        close_price = event.close_price
        max = trade.get('max')
        min = trade.get('min')
        profit_pips = event.pips or profit_pip(trade.get('instrument'), trade.get('open_price'), close_price,
                                               trade.get('side'))
        profit_missed = max - profit_pips
        trade['profit_missed'] = profit_missed
        trade['entry_accuracy'] = round(1 - (abs(min) / (max - min)), 3)
        trade['exit_accuracy'] = round(1 - (profit_missed / (max - min)), 3)
        trade['risk'] = round(max / abs(min), 3) if min else max
        trade['close_price'] = close_price
        trade['close_time'] = close_time
        trade['profit_pips'] = profit_pips
        # trade['drawdown'] =

        trade['profitable_time'] = round(trade['profitable_seconds'] / (close_time - trade['open_time']).seconds, 3)
        logger.info('[Trade_Manage] trade closed=%s' % trade)

        self.save_to_db()
        self.pop_trade(event.trade_id)
        self.saved_to_redis()
        tg.send_me(
            '[FOREX_TRADE_CLOSE_ANALYSIS]\n%s, profit_missed=%s, entry_accuracy=%s, exit_accuracy=%s, risk=%s' % (
                event.trade_id,
                trade['profit_missed'],
                trade['entry_accuracy'],
                trade['exit_accuracy'],
                trade['risk']))

    def update_profitable_seconds(self, trade):
        delta = datetime.utcnow() - trade['last_profitable_start']
        trade['profitable_seconds'] += delta.seconds
        trade['last_profitable_start'] = None

    def heartbeat(self, event):
        for id, trade in self.account.get_trades().items():
            if str(id) not in self.trades:
                self._load_trade(id, trade)

        for trade_id, trade in self.trades.items():
            total_time = datetime.utcnow() - trade['open_time']
            last_profit_period = 0
            if trade['last_profitable_start']:
                last_profit_period = (datetime.utcnow() - trade['last_profitable_start']).seconds

            total_profit_seconds = trade['profitable_seconds'] + last_profit_period
            trade['profitable_time'] = round(total_profit_seconds / float(total_time.seconds), 3)
        system_redis.set(OPENING_TRADE_COUNT_KEY, len(self.trades))
        self.saved_to_redis()

        if not event.counter % (30 * int(1 / settings.LOOP_SLEEP)):  # 30 secs
            self.save_to_db()

        if not event.counter % (60 * 15 * int(1 / settings.LOOP_SLEEP)):  # 15 mins
            if settings.DEBUG:
                print(self.trades)
            else:
                for trade_id, trade in self.trades.items():
                    logger.info(
                        '[Trade_Monitor] %s@%s: max=%s, min=%s, current=%s, last_profit=%s, profit_seconds=%s, profitable_time=%s, last_tick=%s' % (
                            trade_id, trade['instrument'], trade['max'], trade['min'], trade['current'],
                            trade['last_profitable_start'],
                            trade['profitable_seconds'], trade['profitable_time'], trade['last_tick_time']))

    def load_trades(self):
        logger.info('[Trade_Manage] loading %s trades.' % len(self.account.get_trades()))
        if self.account and self.account.broker == 'FXCM':
            for trade_id, trade in self.account.get_trades().items():
                if str(trade_id) in self.trades:
                    continue
                self._load_trade(trade_id, trade)
            for key in self.trades.keys():
                if int(key) not in self.account.get_trades():
                    self.pop_trade(key)
        else:
            raise NotImplementedError

        # restore old data from redis
        redis_data = system_redis.get(TRADES_KEY)
        if redis_data:
            redis_data = json.loads(redis_data)

            for k, v in redis_data.items():
                if k in self.trades:
                    self.trades[k]['max'] = Decimal(str(redis_data[k]['max']))
                    self.trades[k]['min'] = Decimal(str(redis_data[k]['min']))
                    self.trades[k]['profitable_seconds'] = redis_data[k]['profitable_seconds']
                    self.trades[k]['last_profitable_start'] = str_to_datetime(redis_data[k]['last_profitable_start'])
                    total_time = datetime.utcnow() - self.trades[k]['open_time']
                    last_profit_period = 0
                    if self.trades[k]['last_profitable_start']:
                        last_profit_period = (datetime.utcnow() - self.trades[k]['last_profitable_start']).seconds
                    total_profit_seconds = self.trades[k]['profitable_seconds'] + last_profit_period
                    self.trades[k]['profitable_time'] = round(total_profit_seconds / float(total_time.seconds), 3)

        if settings.DEBUG:
            if self.trades:
                print(self.trades)

    def _load_trade(self, trade_id, trade):
        self.trades[str(trade_id)] = {
            'broker': self.account.broker,
            'account_id': self.account.account_id,
            'trade_id': trade.get_tradeId(),
            'instrument': get_mt4_symbol(trade.get_currency()),
            'side': OrderSide.BUY if trade.get_isBuy() else OrderSide.SELL,
            'open_time': trade.get_time(),
            'open_price': Decimal(str(trade.get_open())),
            'take_profit': Decimal(str(trade.get_limit())),
            'stop_loss': Decimal(str(trade.get_stop())),
            'current': 0,
            'max': 0,
            'min': 0,
            'profitable_seconds': 0,
            'last_profitable_start': None,
            'last_tick_time': None,
        }

    def save_to_db(self):
        for trade_id, trade_data in self.trades.items():
            trade = Trade.objects.filter(account_id=trade_data.get('account_id'),
                                         trade_id=trade_id).first()
            if not trade:
                trade = Trade(trade_id=trade_id,
                              broker=trade_data.get('broker'),
                              account_id=trade_data.get('account_id'),
                              side=trade_data.get('side'),
                              open_price=trade_data.get('open_price'),
                              open_time=trade_data.get('open_time'),
                              instrument=trade_data.get('instrument'))
                trade.save()

            if trade_data.get('current'):
                trade.pips = Decimal(str(trade_data['current']))
            if trade_data.get('max'):
                trade.max_profit = Decimal(str(trade_data['max']))
            if trade_data.get('min'):
                trade.min_profit = Decimal(str(trade_data['min']))

            trade.save()

    def saved_to_redis(self):
        data = {}
        for trade_id, trade in self.trades.items():
            data[trade_id] = {'max': float(trade['max']),
                              'min': float(trade['min']),
                              'current': float(trade['current']),
                              'instrument': trade['instrument'],
                              'last_profitable_start': datetime_to_str(trade['last_profitable_start']),
                              'profitable_seconds': int(trade['profitable_seconds'])}

        system_redis.set(TRADES_KEY, json.dumps(data))

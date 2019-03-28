import json
import logging
import time
from datetime import timedelta, datetime
from decimal import Decimal

import settings
from event.event import TickPriceEvent, TradeOpenEvent, TradeCloseEvent, StartUpEvent, HeartBeatEvent
from event.handler import BaseHandler
from mt4.constants import profit_pip, OrderSide, get_mt4_symbol
from utils.redis import system_redis, OPENING_TRADE_COUNT_KEY
from utils.time import datetime_to_timestamp, datetime_to_str, str_to_datetime

logger = logging.getLogger(__name__)
TRADES_KEY = 'TRADES'


class TradeManageHandler(BaseHandler):
    subscription = [TickPriceEvent.type, TradeOpenEvent.type, TradeCloseEvent.type, StartUpEvent.type,
                    HeartBeatEvent.type]
    trades = {}

    def process(self, event):
        if event.type == TickPriceEvent.type:
            self.process_price(event)
        elif event.type == TradeOpenEvent.type:
            self.trade_open(event)
        elif event.type == TradeCloseEvent.type:
            self.trade_close(event)
        elif event.type == StartUpEvent.type:
            self.load_trades()
        elif event.type == HeartBeatEvent.type:
            self.heartbeat(event)

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
            trade['max'] = 0
            trade['min'] = 0
            trade['current'] = 0
            trade['profitable_seconds'] = 0
            trade['last_profitable_start'] = None
            trade['last_tick_time'] = None
            trade['start_from'] = datetime.utcnow()

            self.trades[trade_id] = trade

        system_redis.set(OPENING_TRADE_COUNT_KEY, len(self.trades))

    def trade_close(self, event):
        trade = self.pop_trade(event.trade_id)
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
        # trade['drawdown'] =

        trade['profitable_time'] = round(trade['profitable_seconds'] / (close_time - trade['open_time']).seconds, 3)
        logger.info('[Trade_Manage] trade closed=%s' % trade)
        # todo store into db

    def update_profitable_seconds(self, trade):
        delta = datetime.utcnow() - trade['last_profitable_start']
        trade['profitable_seconds'] += delta.seconds
        trade['last_profitable_start'] = None

    def heartbeat(self, event):
        if not event.counter % (120 * settings.HEARTBEAT / settings.LOOP_SLEEP):
            if settings.DEBUG:
                print(self.trades)
            else:
                for trade_id, trade in self.trades.items():
                    total_time = datetime.utcnow() - trade['start_from']
                    last_profit_period = 0
                    if trade['last_profitable_start']:
                        last_profit_period = datetime.utcnow() - trade['last_profitable_start']
                    total_profit_seconds = trade['profitable_seconds'] + last_profit_period.seconds
                    trade['profitable_time'] = round(total_profit_seconds / float(total_time.seconds), 3)
                    logger.info(
                        '[Trade_Monitor] %s: max=%s, min=%s, current=%s, last_profit=%s, profit_seconds=%s, profitable_time=%s, last_tick=%s' % (
                            trade_id, trade['max'], trade['min'], trade['current'],trade['last_profitable_start'],
                            trade['profitable_seconds'], trade['profitable_time'], trade['last_tick_time']))
                system_redis.set(OPENING_TRADE_COUNT_KEY, len(self.trades))
                self.saved_to_redis()

    def load_trades(self):
        logger.info('[Trade_Manage] loading trades.')
        if self.account.broker == 'FXCM':
            for trade_id, trade in self.account.get_trades().items():
                if str(trade_id) in self.trades:
                    continue
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
                    'max': 0,
                    'min': 0,
                    'profitable_seconds': 0,
                    'last_profitable_start': None,
                    'last_tick_time': None,
                    'start_from': datetime.utcnow()
                }
        else:
            raise NotImplementedError

        # restore old data from redis
        redis_data = system_redis.get(TRADES_KEY)
        if redis_data:
            redis_data = json.loads(redis_data)

            for k, v in redis_data:
                if k in self.trades:
                    self.trades[k]['max'] = Decimal(redis_data[k]['max'])
                    self.trades[k]['min'] = Decimal(redis_data[k]['min'])
                    self.trades[k]['profitable_time'] = redis_data[k]['profitable_time']
                    self.trades[k]['last_profitable_start'] = str_to_datetime(redis_data[k]['last_profitable_start'])

        if settings.DEBUG:
            if self.trades:
                print(self.trades)

    def saved_to_redis(self):
        data = {}
        for trade_id, trade in self.trades:
            data[trade_id] = {'max': float(trade['max']),
                              'min': float(trade['min']),
                              'last_profitable_start': datetime_to_str(trade['last_profitable_start']),
                              'profitable_time': int(trade['profitable_time'])}

        system_redis.set(TRADES_KEY, json.dumps(data))

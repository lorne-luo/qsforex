import json
import logging
import time
from datetime import datetime
from decimal import Decimal

from fxcmpy import fxcmpy, fxcmpy_closed_position

import settings
from broker import SingletonFXCM
from broker.base import AccountType
from broker.fxcm.constants import get_fxcm_symbol
from event.event import TickPriceEvent, TimeFrameEvent, HeartBeatEvent, StartUpEvent, ConnectEvent, TradeCloseEvent, \
    MarketEvent, MarketAction
from event.runner import StreamRunnerBase
from mt4.constants import get_mt4_symbol, OrderSide
from utils import telegram as tg
from utils.market import is_market_open
from utils.redis import price_redis, RedisQueue
from utils.redis import set_last_tick
from utils.telstra_api_v2 import send_to_admin

logger = logging.getLogger(__name__)


class FXCMStreamRunner(StreamRunnerBase):
    account = None
    broker = 'FXCM'
    max_prices = 4000
    loop_counter = 0
    market_open = True

    def __init__(self, queue, *, pairs, handlers, access_token=None, account_type=AccountType.DEMO, api=None, **kwargs):
        super(FXCMStreamRunner, self).__init__(queue=queue, pairs=pairs)
        server = 'real' if account_type == AccountType.REAL else 'demo'
        self.market_open = is_market_open()
        handlers = handlers or []
        try:
            self.fxcm = api or fxcmpy(access_token=access_token, server=server)
            self.fxcm.set_max_prices(self.max_prices)
            self.register(*handlers)
            self.subscribe_pair()
        except Exception as ex:
            if self.market_open:
                logger.error('Start error: %s' % ex)
            else:
                logger.info('Market is closed, init error skiped')

    def run(self):
        logger.info('%s statup.' % self.__class__.__name__)
        logger.info('Registered handler: %s' % ', '.join([x.__class__.__name__ for x in self.handlers]))

        self.pairs = [get_fxcm_symbol(pair) for pair in self.pairs]
        pair_list = ",".join(self.pairs)
        logger.info('Pairs: %s' % pair_list)
        logger.info('####################################')

        while self.running:
            while self.market_open:
                event = self.get(False)
                if event:
                    if event.type == ConnectEvent.type:
                        self.process_connect_event(event)
                    else:
                        self.handle_event(event)
                else:
                    break

            time.sleep(settings.LOOP_SLEEP)
            self.loop_counter += 1

            self.set_market_open()

            if self.market_open:
                self.generate_heartbeat()
                self.check_connection()

    def set_market_open(self):
        current_status = is_market_open()
        if self.market_open != current_status:
            if current_status:
                event = MarketEvent(MarketAction.OPEN)
                self.handle_event(event)
                logger.info('[MarketEvent] Market opened.')
                tg.send_me('[MarketEvent] Market opened.')
            else:
                event = MarketEvent(MarketAction.CLOSE)
                self.handle_event(event)
                logger.info('[MarketEvent] Market closed.')
                tg.send_me('[MarketEvent] Market closed.')
            self.market_open = current_status

    def generate_heartbeat(self):
        if not self.loop_counter % (settings.HEARTBEAT / settings.LOOP_SLEEP):
            self.put(HeartBeatEvent(self.loop_counter))
            if not self.initialized:
                self.initialized = True
                self.put(StartUpEvent())

    def check_connection(self):
        if self.loop_counter % (12 * settings.HEARTBEAT / settings.LOOP_SLEEP):
            # check connection every minute
            return

        if not self.fxcm.is_connected():
            logger.error('[Connect_Lost] disconnected=%s, thread.is_alive=%s' % (
                self.fxcm.__disconnected__, self.fxcm.socket_thread.is_alive()))

            # close and connect again
            self.fxcm.close()
            time.sleep(5)
            self.fxcm.connect()
            self.subscribe_pair()
            logger.info('[Check_Connection] Closed and Reconnected')

    def reconnect(self):
        retry = 11
        count = 1
        while not self.fxcm.is_connected() and count < retry:
            self.fxcm.__reconnect__(count)
            count += 1
            time.sleep(settings.HEARTBEAT)
        else:
            if not self.fxcm.is_connected():
                logger.error('[System Exit] Cant connect to server')
                send_to_admin('[System Exit] Cant connect to server')
            else:
                logger.info('Reconnected')

    def process_connect_event(self, event):
        if event.action == 'CONNECT':
            self.fxcm.connect()
        elif event.action == 'RECONNECT':
            self.reconnect()
        elif event.action == 'DISCONNECT':
            self.fxcm.close()

        logger.info('[ConnectEvent] %s' % event.action)

    def subscribe_pair(self):
        # for symbol in ALL_SYMBOLS:
        #     if symbol not in self.pairs:
        #         self.fxcm.unsubscribe_instrument(symbol)

        if not self.pairs:
            logger.info('No valid FXCM symbol exists.')
            return
        for pair in self.pairs:
            self.fxcm.subscribe_market_data(pair, (self.tick_data,))
            self.fxcm.subscribe_instrument(pair)

        self.fxcm.subscribe_data_model('ClosedPosition', [self.trade_closed])

    def subscribe_data(self):
        # all_models['Offer', 'Account', 'Order', 'OpenPosition', 'ClosedPosition', 'Summary', 'Properties', 'LeverageProfile']
        models = ['Account', 'Order', 'OpenPosition', 'Summary']
        for model in models:
            self.fxcm.subscribe_data_model(model, (self.model_event,))

    def unsubscribe_pair(self, pair):
        self.fxcm.unsubscribe_market_data(pair)
        self.fxcm.unsubscribe_instrument(pair)

    def unsubscribe_all(self):
        for pair in self.pairs:
            self.fxcm.unsubscribe_market_data(pair)
            self.fxcm.unsubscribe_instrument(pair)

        # ['Offer', 'Account', 'Order', 'OpenPosition', 'ClosedPosition', 'Summary', 'Properties', 'LeverageProfile']
        for model in self.fxcm.models:
            self.fxcm.unsubscribe_data_model(model)

    def model_event(self, data):
        # todo send event
        print('Model Event: %s' % data)

    def tick_data(self, data, dataframe):
        try:
            instrument = get_mt4_symbol(data['Symbol'])
            time = datetime.utcfromtimestamp(int(data['Updated']) / 1000.0)

            bid = Decimal(str(data['Rates'][0]))
            ask = Decimal(str(data['Rates'][1]))
            tick = TickPriceEvent(self.broker, instrument, time, bid, ask)
            self.put(tick)
            price_redis.set('%s_TICK' % instrument.upper(),
                            json.dumps(
                                {'ask': float(ask), 'bid': float(bid), 'time': time.strftime('%Y-%m-%d %H:%M:%S:%f')}))
            set_last_tick(time.strftime('%Y-%m-%d %H:%M:%S:%f'))
        except Exception as ex:
            logger.error('tick_data error = %s' % ex)

    def stop(self):
        self.fxcm.close()
        super(FXCMStreamRunner, self).stop()

    def trade_closed(self, data):
        # fixme should not be here
        if 'tradeId' in data and data['tradeId'] != '':
            trade_id = int(data['tradeId'])
            if 'action' in data and data['action'] == 'I':
                closed_trade = fxcmpy_closed_position(self, data)

                event = TradeCloseEvent(
                    broker=self.broker,
                    account_id=self.fxcm.default_account,
                    trade_id=trade_id,
                    instrument=closed_trade.get_currency(),
                    side=OrderSide.BUY if closed_trade.get_isBuy() else OrderSide.SELL,
                    lots=closed_trade.get_amount(),
                    profit=closed_trade.get_grossPL(),
                    close_time=closed_trade.get_close_time(),
                    close_price=closed_trade.get_close(),
                    open_time=closed_trade.get_open_time(),
                    pips=closed_trade.get_visiblePL(),
                )
                self.put(event)


if __name__ == '__main__':
    from event.handler import DebugHandler, TimeFrameTicker

    # from broker.fxcm.streaming import *
    queue = RedisQueue('Pricing')
    debug = DebugHandler(queue, events=[TimeFrameEvent.type])
    tft = TimeFrameTicker(queue, timezone=0)
    pairs = ['EUR/USD']
    fxcm = SingletonFXCM(AccountType.DEMO, settings.FXCM_ACCOUNT_ID, settings.FXCM_ACCESS_TOKEN)

    r = FXCMStreamRunner(queue, pairs=pairs, handlers=[debug, tft], api=fxcm.fxcmpy)
    r.run()

import unittest
from datetime import datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from pandas import DataFrame
from v20.transaction import LimitOrderTransaction, OrderCancelTransaction, StopOrderTransaction

import settings
from mt4.constants import OrderSide, PERIOD_M5, pip, calculate_price
from broker import SingletonOANDA
from broker.oanda.common.convertor import units_to_lots
from broker.oanda.common.prints import print_positions
from portfolio.portfolio import OandaV20Portfolio


class TestAccount(unittest.TestCase):
    account = None
    currency = 'EUR_USD'

    def setUp(self):
        self.account = SingletonOANDA(type='DEMO',
                                      account_id=settings.ACCOUNT_ID,
                                      access_token=settings.ACCESS_TOKEN,
                                      application_name=settings.APPLICATION_NAME)

    def test_instrument(self):
        # list_instruments
        instruments = self.account.list_instruments()
        self.assertTrue(isinstance(instruments, dict))
        print(instruments[self.currency])

        # pip unit
        pip_unit = pip(self.currency)
        self.assertEqual(pip_unit, Decimal('0.0001'))
        pips = pip(self.currency,0.00315)
        self.assertEqual(pips, 31.5)

        # calculate_price
        price = calculate_price(1.11325, OrderSide.BUY, 31.4, self.currency)
        self.assertEqual(price, Decimal('1.11639'))

        # get_candle
        from_time = datetime.utcnow()
        to_time = from_time - relativedelta(minutes=101)
        count = 20

        # get_candle
        candles = self.account.get_candle(self.currency, PERIOD_M5, count=count, fromTime=to_time, toTime=to_time)
        self.assertTrue(isinstance(candles, DataFrame))
        self.assertEqual(len(candles), count)

    def test_position(self):
        # pull_position
        success, position = self.account.pull_position(self.currency)
        self.assertTrue(success)
        print_positions([position])

        # list_all_positions
        success, positions = self.account.list_all_positions()
        self.assertTrue(success)
        print_positions(positions)

        # list_open_positions
        success, positions = self.account.list_open_positions()
        self.assertTrue(success)
        print_positions(positions)

        # close_position
        success, detail = self.account.close_position(self.currency)
        self.assertTrue(success)

        # close_all_position
        self.account.close_all_position()

    def test_market_order(self):
        self.account.list_prices()
        self.assertTrue(len(self.account._prices))
        ask = self.account._prices.get(self.currency).get('ask')
        tp_price = calculate_price(ask, OrderSide.BUY, 31.4, self.currency)

        success, trades = self.account.list_trade()
        trade_exists = len(trades)

        success, transactions = self.account.market_order(self.currency, OrderSide.BUY, lots=0.1,
                                                          take_profit=tp_price, stop_loss=40)
        self.assertTrue(success)

        success, trades = self.account.list_trade()
        self.assertEqual(len(trades), trade_exists + 1)

        success, trades = self.account.list_open_trade()
        self.assertTrue(success)
        self.assertTrue(len(trades))

        trade_id = trades[0].id
        success, transactions = self.account.take_profit(trade_id, price='1.33322')
        self.assertTrue(success)

        trade = self.account.get_trade(trade_id)
        self.assertTrue(trade)

        order = self.account.get_order(trade.takeProfitOrder.id)
        self.assertTrue(order)

        orders = self.account.list_order()
        self.assertTrue(orders)

        success, transactions = self.account.take_profit(trade_id, order_id=trade.takeProfitOrder.id, price='1.44444')
        self.assertTrue(success)

        success, transactions = self.account.trailing_stop_loss(trade_id=trade_id, stop_loss_pip=40.1)
        self.assertTrue(success)

        success, transactions = self.account.close(trade_id, lots=0.04)
        self.assertTrue(success)
        success, transactions = self.account.close(trade_id)
        self.assertTrue(success)
        self.assertFalse(trade_id in self.account.trades)

    def test_pending_order(self):
        self.account.list_prices()
        self.assertTrue(len(self.account._prices))
        ask = self.account._prices.get(self.currency).get('ask')
        limit_price = calculate_price(ask, OrderSide.BUY, 31.4, self.currency)

        success, transactions = self.account.limit_order(self.currency, OrderSide.SELL, price=limit_price, lots=0.1)
        self.assertTrue(success)
        self.assertTrue(isinstance(transactions[0], LimitOrderTransaction))

        success, transaction = self.account.cancel_order(transactions[0].id)
        self.assertTrue(success)
        self.assertTrue(isinstance(transaction, OrderCancelTransaction))
        self.assertTrue(transaction.id not in self.account.orders)

        success, transactions = self.account.stop_buy(self.currency, price=limit_price, lots=0.1)
        self.assertTrue(success)
        self.assertTrue(isinstance(transactions[0], StopOrderTransaction))

        success, transaction = self.account.cancel_order(transactions[0].id)
        self.assertTrue(success)
        self.assertTrue(isinstance(transaction, OrderCancelTransaction))
        self.assertTrue(transaction.id not in self.account.orders)


class TestPortifolio(unittest.TestCase):

    def test_oanda_portifolio(self):
        profile = OandaV20Portfolio('practice', settings.ACCESS_TOKEN, '101-011-10496264-002', None)
        units = profile.trade_units('EURUSD', 30)
        print(units_to_lots(units))
        units = profile.trade_units('USDJPY', 30)
        print(units_to_lots(units))

import unittest
from datetime import datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from pandas import DataFrame

import settings
from mt4.constants import OrderSide, PERIOD_M5
from oanda_v20.account import Account
from oanda_v20.common.prints import print_positions


class TestAccount(unittest.TestCase):
    account = None
    currency = 'EUR_USD'

    def setUp(self):
        self.account = Account(settings.ACCOUNT_ID)

    def test_instrument(self):
        # list_instruments
        instruments = self.account.list_instruments()
        self.assertTrue(isinstance(instruments, dict))
        print(instruments[self.currency])

        # pip unit
        pip_unit = self.account.get_pip_unit(self.currency)
        self.assertEqual(pip_unit, Decimal('0.0001'))
        pips = self.account.get_pips(0.00315, self.currency)
        self.assertEqual(pips, 31.5)

        # calculate_price
        price = self.account.calculate_price(1.11325, OrderSide.BUY, 31.4, self.currency)
        self.assertEqual(price, Decimal('1.11639'))

        # get_candle
        from_time = datetime.now()
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

    def test_order(self):
        success, trades = self.account.list_trade()
        trade_exists = len(trades)

        success, transactions = self.account.market_order('EUR_USD', OrderSide.BUY, lots=0.1, stop_loss_pip=40)
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
        
        success, transactions = self.account.take_profit(trade_id, order_id=trade.takeProfitOrder.id, price='1.44444')
        self.assertTrue(success)

        success, transactions = self.account.trailing_stop_loss(trade_id=trade_id, stop_loss_pip=40.1)
        self.assertTrue(success)

        success, transactions = self.account.close('109', lots=0.04)
        self.assertTrue(success)
        success, transactions = self.account.close('109')
        self.assertTrue(success)

    def test_trade(self):
        pass

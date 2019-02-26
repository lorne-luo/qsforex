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
        pass

    def test_trade(self):
        pass

import unittest

import settings
from broker.base import AccountType
from broker import SingletonFXCM
from mt4.constants import OrderSide


class TestAccount(unittest.TestCase):
    account = None
    currency = 'EUR_USD'

    def setUp(self):
        ACCOUNT_ID = 3261139
        ACCESS_TOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'
        self.account = SingletonFXCM(type=AccountType.DEMO,
                                     account_id=ACCOUNT_ID,
                                     access_token=ACCESS_TOKEN)

    def test_instrument(self):
        pass

    def test_market_order(self):
        position_count = len(self.account.open_positions)
        trade_count = len(self.account.list_open_trade())
        # market order
        success, order = self.account.market_order('EUR/USD', OrderSide.BUY, 0.01, take_profit=30, stop_loss=-30)
        self.assertTrue(success)
        self.assertEqual(len(self.account.open_positions), 1 + position_count)
        self.assertEqual(len(self.account.list_open_trade()), 1 + trade_count)

        self.assertTrue(len(self.account.list_all_positions()))
        self.assertTrue(len(self.account.list_all_positions()))

        trade_id = self.account.list_open_trade()[0]
        trade = self.account.get_trade(trade_id)
        self.assertTrue(trade.get_amount())
        self.account.take_profit(self, trade_id, 40, is_in_pips=True)
        self.account.stop_loss(self, trade_id, -40, is_in_pips=True)

        self.account.close_trade(trade_id, 0.005)
        self.assertTrue(len(self.account.list_open_trade()) == 1 + trade_count)
        trade_id = self.account.open_trade_ids()[0]
        self.account.close_trade(trade_id)
        self.assertEqual(len(self.account.list_open_trade()), trade_count)
        self.assertEqual(len(self.account.open_positions), position_count)

        # limit stop order
        order_count = len(self.account.open_order_ids())
        success, order1 = self.account.limit_order('EUR/USD', OrderSide.BUY, 1.1132, 0.1, take_profit=60, stop_loss=-30)
        self.assertTrue(success)
        success, order2 = self.account.stop_order('EUR/USD', OrderSide.SELL, 1.1139, 0.1, take_profit=60, stop_loss=-30)
        self.assertTrue(success)
        self.assertEqual(len(self.account.open_order_ids()), 2 + order_count)

        self.account.take_profit(self, order1.get_orderId(), 40, is_in_pips=True)
        self.account.stop_loss(self, order2.get_orderId(), -40, is_in_pips=True)

        self.account.cancel_order(order1.get_orderId())
        self.account.cancel_order(order2.get_orderId())
        self.assertEqual(len(self.account.open_order_ids()), order_count)

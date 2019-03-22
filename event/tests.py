import unittest
import json
from broker.oanda.common.constants import OrderType
from event.event import SignalEvent, SignalAction, Event
from mt4.constants import OrderSide, PERIOD_M5, pip, calculate_price
from strategy.hlhb_trend import HLHBTrendStrategy


class EventTest(unittest.TestCase):

    def test_event(self):
        open = SignalEvent(SignalAction.OPEN,
                           HLHBTrendStrategy.name, HLHBTrendStrategy.version,
                           HLHBTrendStrategy.magic_number,
                           instrument='EURUSD',
                           side=OrderSide.BUY,
                           order_type=OrderType.MARKET,
                           stop_loss=30,
                           take_profit=50,
                           trailing_stop=None,
                           percent=None)
        close = SignalEvent(SignalAction.CLOSE,
                            HLHBTrendStrategy.name, HLHBTrendStrategy.version,
                            HLHBTrendStrategy.magic_number,
                            instrument='EURUSD',
                            side=OrderSide.BUY,
                            percent=0.5)

        data = json.dumps(open.to_dict())
        data2 = json.loads(data)
        open2 = Event.from_dict(data2)

        self.assertEqual(open.type, open2.type)
        for k in open.__dict__.keys():
            self.assertEqual(open.__dict__[k], open2.__dict__[k])

        data = json.dumps(close.to_dict())
        data2 = json.loads(data)
        close2 = Event.from_dict(data2)

        self.assertEqual(close.type, close2.type)
        for k in close.__dict__.keys():
            self.assertEqual(close.__dict__[k], close2.__dict__[k])

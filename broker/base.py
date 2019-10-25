from mt4.constants import OrderSide


class AccountType(object):
    REAL = 'REAL'
    DEMO = 'DEMO'
    SANDBOX = 'SANDBOX'


class BrokerAccount(object):
    broker = ''
    type = AccountType.DEMO
    name = ''
    account_id = ''
    access_token = ''
    default_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCNH', 'XAUUSD']

    @property
    def id(self):
        return '%s#%s#%s' % (self.broker, self.account_id, self.access_token)

    def __init__(self, *args, **kwargs):
        self.broker = self.broker or self.__class__.__name__
        self.name = self.id


class PositionBase(object):

    def pull_position(self, instrument):
        raise NotImplementedError

    def list_open_positions(self):
        raise NotImplementedError

    def list_all_positions(self):
        raise NotImplementedError

    def close_all_position(self):
        raise NotImplementedError

    def close_position(self, instrument, longUnits='ALL', shortUnits='ALL'):
        raise NotImplementedError


class OrderBase(object):

    def list_order(self, ids=None, state=None, instrument=None, count=20, beforeID=None):
        raise NotImplementedError

    def list_pending_order(self):
        raise NotImplementedError

    def get_order(self, order_id):
        raise NotImplementedError

    def limit_order(self, instrument, side, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        raise NotImplementedError

    def limit_buy(self, instrument, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        return self.limit_order(instrument=instrument, side=OrderSide.BUY, price=price,
                                lots=lots,
                                take_profit=take_profit,
                                stop_loss=stop_loss,
                                trailing_pip=trailing_pip,
                                **kwargs)

    def limit_sell(self, instrument, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        return self.limit_order(instrument=instrument, side=OrderSide.SELL, price=price,
                                lots=lots,
                                take_profit=take_profit,
                                stop_loss=stop_loss,
                                trailing_pip=trailing_pip,
                                **kwargs)

    def stop_order(self, instrument, side, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        raise NotImplementedError

    def stop_buy(self, instrument, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        """buy shortcut for stop order"""
        return self.stop_order(instrument=instrument, side=OrderSide.BUY, price=price, lots=lots,
                               take_profit=take_profit,
                               stop_loss=stop_loss, trailing_pip=trailing_pip, **kwargs)

    def stop_sell(self, instrument, price, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        """sell shortcut for stop order"""
        return self.stop_order(instrument=instrument, side=OrderSide.SELL, price=price, lots=lots,
                               take_profit=take_profit, stop_loss=stop_loss, trailing_pip=trailing_pip, **kwargs)

    def market_order(self, instrument, side, lots, take_profit=None, stop_loss=None, trailing_pip=None, **kwargs):
        raise NotImplementedError

    def take_profit(self, trade_id, price, **kwargs):
        raise NotImplementedError

    def stop_loss(self, trade_id, price, **kwargs):
        raise NotImplementedError

    def trailing_stop_loss(self, trade_id, pips, **kwargs):
        raise NotImplementedError

    def cancel_order(self, order_id, **kwargs):
        raise NotImplementedError


class TradeBase(object):
    def list_trade(self, ids=None, state=None, instrument=None, count=20, beforeID=None):
        raise NotImplementedError

    def list_open_trade(self):
        raise NotImplementedError

    def get_trade(self, trade_id):
        raise NotImplementedError

    def close_trade(self, trade_id, lots=None, percent=None):
        raise NotImplementedError


class InstrumentBase(object):
    @property
    def instruments(self):
        if self._instruments:
            return self._instruments
        else:
            return self.list_instruments()

    def list_instruments(self):
        raise NotImplementedError


class PriceBase(object):

    def list_prices(self, instruments=None, since=None, includeUnitsAvailable=True):
        raise NotImplementedError

    def get_price(self, instrument, type='mid'):
        raise NotImplementedError

    def get_candle(self, instrument, granularity, count=50, fromTime=None, toTime=None, price_type='M', smooth=False):
        raise NotImplementedError

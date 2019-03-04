from mt4.constants import OrderSide
from utils.singleton import SingletonDecorator


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

    def limit_order(self, instrument, side, price,
                    lots, timeInForce,
                    positionFill,
                    trigger_condition,
                    gtd_time=None,
                    take_profit_price=None,
                    stop_loss_pip=None,
                    trailing_pip=None,
                    order_id=None,  # order to replace
                    client_id=None, client_tag=None, client_comment=None):
        raise NotImplementedError

    def limit_buy(self, instrument, price,
                  lots, timeInForce,
                  positionFill,
                  trigger_condition,
                  gtd_time=None,
                  take_profit_price=None,
                  stop_loss_pip=None,
                  trailing_pip=None,
                  order_id=None,
                  client_id=None, client_tag=None, client_comment=None):
        return self.limit_order(instrument=instrument, side=OrderSide.BUY, price=price,
                                lots=lots, timeInForce=timeInForce,
                                positionFill=positionFill,
                                trigger_condition=trigger_condition,
                                gtd_time=gtd_time,
                                take_profit_price=take_profit_price,
                                stop_loss_pip=stop_loss_pip,
                                trailing_pip=trailing_pip,
                                order_id=order_id,
                                client_id=client_id, client_tag=client_tag, client_comment=client_comment)

    def limit_sell(self, instrument, price,
                   lots, timeInForce,
                   positionFill,
                   trigger_condition,
                   gtd_time=None,
                   take_profit_price=None,
                   stop_loss_pip=None,
                   trailing_pip=None,
                   order_id=None,  # order to replace
                   client_id=None, client_tag=None, client_comment=None):
        return self.limit_order(instrument=instrument, side=OrderSide.SELL, price=price,
                                lots=lots, timeInForce=timeInForce,
                                positionFill=positionFill,
                                trigger_condition=trigger_condition,
                                gtd_time=gtd_time,
                                take_profit_price=take_profit_price,
                                stop_loss_pip=stop_loss_pip,
                                trailing_pip=trailing_pip,
                                order_id=order_id,
                                client_id=client_id, client_tag=client_tag, client_comment=client_comment)

    def stop_order(self, instrument, side, price,
                   lots, timeInForce,
                   positionFill, priceBound,
                   trigger_condition,
                   gtd_time=None,
                   take_profit_price=None,
                   stop_loss_pip=None,
                   trailing_pip=None,
                   order_id=None,  # order to replace
                   client_id=None, client_tag=None, client_comment=None):
        raise NotImplementedError

    def stop_buy(self, instrument, price,
                 lots, timeInForce,
                 positionFill, priceBound,
                 trigger_condition,
                 gtd_time=None,
                 take_profit_price=None,
                 stop_loss_pip=None,
                 trailing_pip=None,
                 order_id=None,  # order to replace
                 client_id=None, client_tag=None, client_comment=None):
        """buy shortcut for stop order"""
        return self.stop_order(instrument=instrument, side=OrderSide.BUY, price=price,
                               lots=lots, timeInForce=timeInForce, priceBound=priceBound,
                               positionFill=positionFill,
                               trigger_condition=trigger_condition,
                               gtd_time=gtd_time,
                               take_profit_price=take_profit_price,
                               stop_loss_pip=stop_loss_pip,
                               trailing_pip=trailing_pip,
                               order_id=order_id,
                               client_id=client_id, client_tag=client_tag, client_comment=client_comment)

    def stop_sell(self, instrument, price,
                  lots, timeInForce,
                  positionFill, priceBound,
                  trigger_condition,
                  gtd_time=None,
                  take_profit_price=None,
                  stop_loss_pip=None,
                  trailing_pip=None,
                  order_id=None,  # order to replace
                  client_id=None, client_tag=None, client_comment=None):
        """sell shortcut for stop order"""
        return self.stop_order(instrument=instrument, side=OrderSide.SELL, price=price,
                               lots=lots, timeInForce=timeInForce, priceBound=priceBound,
                               positionFill=positionFill,
                               trigger_condition=trigger_condition,
                               gtd_time=gtd_time,
                               take_profit_price=take_profit_price,
                               stop_loss_pip=stop_loss_pip,
                               trailing_pip=trailing_pip,
                               order_id=order_id,
                               client_id=client_id, client_tag=client_tag, client_comment=client_comment)

    def market_order(self, instrument, side,
                     lots, timeInForce,
                     priceBound, positionFill,
                     take_profit_price=None,
                     stop_loss_pip=None,
                     trailing_pip=None,
                     client_id=None, client_tag=None, client_comment=None,
                     trade_client_id=None, trade_client_tag=None, trade_client_comment=None):
        raise NotImplementedError

    def market_if_touched(self, instrument, side, price, lots,
                          priceBound, timeInForce,
                          gtd_time, positionFill,
                          trigger_condition,
                          take_profit_price=None,
                          stop_loss_pip=None,
                          trailing_pip=None,
                          order_id=None,  # order to replace
                          client_id=None, client_tag=None, client_comment=None,
                          trade_client_id=None, trade_client_tag=None, trade_client_comment=None):
        raise NotImplementedError

    def take_profit(self, trade_id, price, order_id, client_trade_id,
                    timeInForce, gtd_time,
                    trigger_condition,
                    client_id=None, client_tag=None, client_comment=None):
        raise NotImplementedError

    def stop_loss(self, trade_id, stop_loss_pip, price, order_id, client_trade_id,
                  timeInForce, gtd_time,
                  trigger_condition,
                  guaranteed=None,
                  client_id=None, client_tag=None, client_comment=None):
        raise NotImplementedError

    def trailing_stop_loss(self, trade_id, stop_loss_pip, order_id, client_trade_id,
                           timeInForce, gtd_time,
                           trigger_condition,
                           client_id=None, client_tag=None, client_comment=None):
        raise NotImplementedError

    def cancel_order(self, order_id):
        raise NotImplementedError


class TradeBase(object):
    def list_trade(self, ids=None, state=None, instrument=None, count=20, beforeID=None):
        raise NotImplementedError

    def list_open_trade(self):
        raise NotImplementedError

    def get_trade(self, trade_id):
        raise NotImplementedError

    def close(self, trade_id, lots='ALL'):
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

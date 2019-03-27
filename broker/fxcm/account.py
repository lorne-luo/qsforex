import json
import logging
from decimal import Decimal

from fxcmpy import fxcmpy

import settings
from broker.base import BrokerAccount, AccountType
from broker.fxcm.constants import get_fxcm_symbol
from broker.fxcm.instrument import InstrumentMixin
from broker.fxcm.order import OrderMixin
from broker.fxcm.position import PositionMixin
from broker.fxcm.price import PriceMixin
from broker.fxcm.trade import TradeMixin
from broker.oanda.common.convertor import units_to_lots
from mt4.constants import pip, get_mt4_symbol
from utils.redis import price_redis
from utils.string import format_dict

logger = logging.getLogger(__name__)


class FXCM(PositionMixin, OrderMixin, TradeMixin, InstrumentMixin, PriceMixin, BrokerAccount):
    broker = 'FXCM'
    max_prices = 2000
    pairs = BrokerAccount.default_pairs
    MAX_CANDLES = 10000

    def __init__(self, type, account_id, access_token, *args, **kwargs):
        self.type = 'real' if type == AccountType.REAL else 'demo'
        self.account_id = int(account_id)
        self.access_token = access_token
        super(FXCM, self).__init__(*args, **kwargs)
        server = 'real' if type == AccountType.REAL else 'demo'

        if not access_token:
            self.fxcmpy = kwargs.get('fxcmapi')
        else:
            self.fxcmpy = fxcmpy(access_token=access_token, server=server)
        self.fxcmpy.set_max_prices(self.max_prices)

        if self.account_id != self.fxcmpy.default_account:
            self.fxcmpy.set_default_account(self.account_id)

    @property
    def summary(self):
        for account in self.fxcmpy.get_accounts('list'):
            if account['accountId'] == str(self.account_id):
                return account
        return None

    def dump(self):
        print(self.summary)

    def get_equity(self):
        summarys = self.fxcmpy.get_accounts('list')
        for s in summarys:
            if str(s.get('accountId')) == str(self.account_id):
                equity = s.get('equity')
                return Decimal(str(equity))

        raise Exception('Cant get equity.')

    def get_lots(self, instrument, stop_loss_pips=None, risk_ratio=Decimal('0.05')):
        max_trade = 5
        if len(self.get_trades() >= max_trade):
            return 0

        equity = self.get_equity()
        if not stop_loss_pips:
            return equity / 1000 * Decimal('0.1')

        instrument = get_fxcm_symbol(instrument)
        pip_unit = pip(instrument)

        risk = equity * risk_ratio
        value = risk / stop_loss_pips / pip_unit

        if instrument.upper().endswith('USD'):
            price = self.get_price(instrument)
            value = value * price
        elif instrument.upper().startswith('USD'):
            lots = equity / 1000 * Decimal('0.1')
            return lots.quantize(Decimal("0.01"))
        else:
            # cross pair
            raise NotImplementedError
        units = int(value / 100) * 100
        return units_to_lots(units).quantize(Decimal("0.01"))

    def log_account(self):
        logger.info('[LOG_ACCOUNT]')
        content = format_dict(self.summary)

        if settings.DEBUG:
            print(content)
        else:
            logger.info(content)


if __name__ == '__main__':
    #    from broker.fxcm.account import *
    fxcm = FXCM(AccountType.DEMO, settings.FXCM_ACCOUNT_ID, settings.FXCM_ACCESS_TOKEN)

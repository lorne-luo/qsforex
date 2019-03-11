import fxcmpy

from broker.base import BrokerAccount, AccountType
from broker.fxcm.constants import SingletonFXCMAPI, FXCM_CONFIG
from broker.fxcm.instrument import InstrumentMixin
from broker.fxcm.order import OrderMixin
from broker.fxcm.position import PositionMixin
from broker.fxcm.price import PriceMixin
from broker.fxcm.trade import TradeMixin


class FXCM(PositionMixin, OrderMixin, TradeMixin, InstrumentMixin, PriceMixin, BrokerAccount):
    broker = 'FXCM'
    MAX_PRICES = 2000
    pairs = BrokerAccount.default_pairs

    def __init__(self, type, account_id, access_token, *args, **kwargs):
        self.type = 'real' if type == AccountType.REAL else 'demo'
        self.account_id = account_id
        self.access_token = access_token
        super(FXCM, self).__init__(*args, **kwargs)
        server = 'real' if type == AccountType.REAL else 'demo'
        self.fxcmpy = SingletonFXCMAPI(access_token=access_token,
                                       server=server,
                                       log_level=FXCM_CONFIG.get('debugLevel', 'ERROR'),
                                       log_file=FXCM_CONFIG.get('logpath'))
        self.fxcmpy.set_max_prices(self.MAX_PRICES)
        self.fxcmpy.set_default_account(self.account_id)

    @property
    def summary(self):
        result={}
        for k,v in self.fxcmpy.get_accounts().T.to_dict().items():
            result[v['accountId']]=v
        return result

    def dump(self):
        print(self.summary)

if __name__ == '__main__':
    ACCOUNT_ID = 3261139
    ACCESS_TOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'
    fxcm = FXCM(AccountType.DEMO, ACCOUNT_ID, ACCESS_TOKEN)

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
        return '%s_%s_%s' % (self.broker, self.account_id, self.access_token)

    def __init__(self, *args, **kwargs):
        self.broker = self.broker or self.__class__.__name__
        self.name = self.id


SingletonBrokerAccount = SingletonDecorator(BrokerAccount)

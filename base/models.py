class AccountType(object):
    LIVE = 'LIVE'
    DEMO = 'DEMO'
    SANDBOX = 'SANDBOX'


class AccountBase(object):
    broker = None
    type = None
    name = None
    account_id = None
    DEFAULT_CURRENCIES = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCNH', 'XAUUSD']

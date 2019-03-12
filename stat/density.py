import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN

from dateutil.relativedelta import relativedelta

from broker.base import AccountType
from broker.fxcm.account import FXCM
from mt4.constants import PIP_DICT

ACCOUNT_ID = 3261139
ACCESS_TOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'
fxcm = FXCM(AccountType.DEMO, ACCOUNT_ID, ACCESS_TOKEN)

first = datetime(2004, 4, 18, 18, 1)

pip_unit = PIP_DICT['EURUSD']
result = {}
start = first
end = first
while end.date() != datetime.now().date():
    end = start + relativedelta(day=10)
    if end > datetime.now():
        end = datetime.now()
    df = fxcm.fxcmpy.get_candles('EURUSD', granularity='m1', fromTime=start, toTime=end, columns=['askhigh', 'bidlow'])
    for index, row in df.iterrows():
        high = Decimal(str(row['askhigh'])).quantize(Decimal('0.0001'), rounding=ROUND_HALF_EVEN)
        low = Decimal(str(row['bidlow'])).quantize(Decimal('0.0001'), rounding=ROUND_HALF_EVEN)

with open('eurusd_density.json', 'a') as f:
    f.write(json.dumps(result))

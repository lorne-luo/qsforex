import json
import numpy as np
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
import matplotlib.pyplot as plt

from dateutil.relativedelta import relativedelta

from broker.base import AccountType
from broker.fxcm.account import FXCM
from broker.fxcm.constants import get_fxcm_symbol
from mt4.constants import PIP_DICT, pip

ACCOUNT_ID = 3261139
ACCESS_TOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'
fxcm = FXCM(AccountType.DEMO, ACCOUNT_ID, ACCESS_TOKEN)

first = datetime(2018, 1, 18, 18, 1)
symbol = 'EURUSD'
pip_unit = PIP_DICT[symbol]
end = datetime.now()
result = {}


def process_df(df):
    for index, row in df.iterrows():
        high = Decimal(str(row['askhigh'])).quantize(pip_unit, rounding=ROUND_HALF_EVEN)
        low = Decimal(str(row['bidlow'])).quantize(pip_unit, rounding=ROUND_HALF_EVEN)
        volume = Decimal(str(row['tickqty']))
        if not volume:
            continue
        distance = pip(symbol, high - low, True)
        avg_vol = (10 / distance).quantize(pip_unit)

        for i in range(int(distance) + 1):
            target = low + i * pip_unit
            if str(target) not in result:
                result[str(target)] = 0
            result[str(target)] += avg_vol


count = 0
while end > first:
    df = fxcm.fxcmpy.get_candles(get_fxcm_symbol(symbol), period='m1', number=10000, end=end,
                                 columns=['askhigh', 'bidlow', 'tickqty'])
    process_df(df)
    count += 1
    print(count, end)

    end = df.iloc[1].name.to_pydatetime() - relativedelta(minutes=1)

for k, v in result.items():
    result[k] = str(v)

output = ''
keylist = result.keys()
keys = sorted(keylist)
for k in keys:
    output += '    %s: %s,\n' % (k, result[k])

with open('eurusd_density_std.json', 'w+') as f:
    f.write('''{
%s
}''' % output)


json_data = open('eurusd_density_weight.json').read()
data = eval(json_data)
current_price = 1.1285
fig = plt.figure()
ax = plt.axes()
items = data.items()
y = [v for k, v in items if pip('EURUSD', k - current_price, True) < 120]
x = [k for k, v in items if pip('EURUSD', k - current_price, True) < 120]
ax.plot(x, y)
plt.axvline(x=current_price,color='r')
plt.xticks(np.arange(min(x), max(x), 0.001), rotation=90)
fig.show()

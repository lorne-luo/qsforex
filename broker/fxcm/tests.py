import requests

import json
from broker.fxcm import fxcm_rest_api
from broker.fxcm.constants import FXCMAccountType


YOURTOKEN = '8a1e87908a70362782ea9744e2c9c82689bde3ac'

trader = fxcm_rest_api.Trader(YOURTOKEN, FXCMAccountType.DEMO,messageHandler=lambda x:print(x))
trader.debug_level = "INFO" # verbose logging... don't set to receive errors only
trader.login()

c =trader.candles("EUR/USD", "m15", 45, dt_fmt="%Y/%m/%d %H:%M:%S")['candles']
print(len(c))
for candle in c:
    print(candle)

trader.subscribe_symbol("EUR/USD", handler=lambda x:print(json.loads(x)))
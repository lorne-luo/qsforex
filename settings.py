from decimal import Decimal
import os
from environs import Env

env = Env()

env.read_env('.env')

DEBUG = env.bool('DEBUG', True)

APPLICATION_NAME = 'qsforex'
BASE_CURRENCY = "USD"
EQUITY = Decimal("1000.00")

OANDA_ENVIRONMENTS = {
    "streaming": {
        "real": "stream-fxtrade.oanda.com",
        "practice": "stream-fxpractice.oanda.com",
        "sandbox": "stream-sandbox.oanda.com"
    },
    "api": {
        "real": "api-fxtrade.oanda.com",
        "practice": "api-fxpractice.oanda.com",
        "sandbox": "api-sandbox.oanda.com"
    }
}

OANDA_DOMAIN = os.environ.get('DOMAIN', 'practice')
OANDA_API_DOMAIN = OANDA_ENVIRONMENTS["api"][OANDA_DOMAIN]
OANDA_STREAM_DOMAIN = OANDA_ENVIRONMENTS["streaming"][OANDA_DOMAIN]
OANDA_ACCESS_TOKEN = os.environ.get('OANDA_ACCESS_TOKEN', None)
OANDA_ACCOUNT_ID = os.environ.get('OANDA_ACCOUNT_ID', None)

CSV_DATA_DIR = os.environ.get('QSFOREX_CSV_DATA_DIR', None)
OUTPUT_RESULTS_DIR = os.environ.get('QSFOREX_OUTPUT_RESULTS_DIR', None)

TELSTRA_CLIENT_KEY = env.str('TELSTRA_CLIENT_KEY', '')
TELSTRA_CLIENT_SECRET = env.str('TELSTRA_CLIENT_SECRET', '')
ADMIN_MOBILE_NUMBER = env.str('ADMIN_MOBILE_NUMBER', '')

REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
PRICE_CHANNEL = 15
SYSTEM_CHANNEL = 14
ORDER_CHANNEL = 12

try:
    from local import *
except ImportError:
    pass

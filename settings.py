from decimal import Decimal
from environs import Env

env = Env()

env.read_env('.env')

DEBUG = env.bool('DEBUG', True)

APPLICATION_NAME = 'qsforex'
BASE_CURRENCY = "USD"
EQUITY = Decimal("1000.00")

OANDA_DOMAIN = env.str('OANDA_DOMAIN', 'DEMO')
OANDA_ACCESS_TOKEN = env.str('OANDA_ACCESS_TOKEN', None)
OANDA_ACCOUNT_ID = env.str('OANDA_ACCOUNT_ID', None)

CSV_DATA_DIR = env.str('QSFOREX_CSV_DATA_DIR', None)
OUTPUT_RESULTS_DIR = env.str('QSFOREX_OUTPUT_RESULTS_DIR', None)

TELSTRA_CLIENT_KEY = env.str('TELSTRA_CLIENT_KEY', '')
TELSTRA_CLIENT_SECRET = env.str('TELSTRA_CLIENT_SECRET', '')
ADMIN_MOBILE_NUMBER = env.str('ADMIN_MOBILE_NUMBER', '')

PLOTLY_USERNAME = env.str('PLOTLY_USERNAME', '')
PLOTLY_API_KEY = env.str('PLOTLY_API_KEY', '')

REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
PRICE_CHANNEL = 15
SYSTEM_CHANNEL = 14
ORDER_CHANNEL = 12

LOOP_SLEEP = 0.5
HEARTBEAT = 5

try:
    from local import *
except ImportError:
    pass

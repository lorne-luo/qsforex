from decimal import Decimal
import os

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

DOMAIN = os.environ.get('DOMAIN', 'practice')
API_DOMAIN = OANDA_ENVIRONMENTS["api"][DOMAIN]
STREAM_DOMAIN = OANDA_ENVIRONMENTS["streaming"][DOMAIN]


CSV_DATA_DIR = os.environ.get('QSFOREX_CSV_DATA_DIR', None)
OUTPUT_RESULTS_DIR = os.environ.get('QSFOREX_OUTPUT_RESULTS_DIR', None)


ACCESS_TOKEN = os.environ.get('OANDA_API_ACCESS_TOKEN', None)
ACCOUNT_ID = os.environ.get('OANDA_API_ACCOUNT_ID', None)

APPLICATION_NAME = 'qsforex'
BASE_CURRENCY = "USD"
EQUITY = Decimal("1000.00")
DEBUG = os.environ.get('DEBUG', False)

try:
    from local import *
except ImportError:
    pass

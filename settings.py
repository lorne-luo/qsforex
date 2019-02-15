from decimal import Decimal
import os

ENVIRONMENTS = {
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

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSV_DATA_DIR = os.environ.get('QSFOREX_CSV_DATA_DIR', '/Users/lorne.luo/Workspace/lorne/qsforex/tick_data/')
OUTPUT_RESULTS_DIR = os.environ.get('QSFOREX_OUTPUT_RESULTS_DIR', '/Users/lorne.luo/Workspace/lorne/qsforex/result/')

DOMAIN = "practice"
STREAM_DOMAIN = ENVIRONMENTS["streaming"][DOMAIN]
API_DOMAIN = ENVIRONMENTS["api"][DOMAIN]
ACCESS_TOKEN = os.environ.get('OANDA_API_ACCESS_TOKEN', None)
ACCOUNT_ID = os.environ.get('OANDA_API_ACCOUNT_ID', None)

BASE_CURRENCY = "USD"
EQUITY = Decimal("1000.00")

try:
    from .local import *
except ImportError:
    pass

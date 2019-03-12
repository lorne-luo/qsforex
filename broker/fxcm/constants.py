from fxcmpy import fxcmpy

from mt4.constants import PERIOD_H1, PERIOD_M1, PERIOD_M5, PERIOD_M15, PERIOD_M30, PERIOD_D1, PERIOD_H4, PERIOD_W1, \
    PERIOD_MN1
from utils.singleton import SingletonDecorator


class FXCMAccountType(object):
    REAL = 'prod'
    DEMO = 'demo'


FXCM_CONFIG = {
    "environments": {
        "demo": {
            "trading": "https://api-demo.fxcm.com",
            "port": 443
        },
        "real": {
            "trading": "https://api.fxcm.com",
            "port": 443
        }
    },
    "logpath": "/tmp/fxcm.log",
    "_debugLevels": "Levels are (from most to least logging) DEBUG, INFO, WARNING, ERROR, CRITICAL",
    "debugLevel": "info",
    "subscription_lists": "#Determines default subscription list of item updates to listen to",
    "subscription_list": ["Offer", "Account", "Order", "OpenPosition", "ClosedPosition", "LeverageProfile", "Summary",
                          "Properties"]
}

ALL_SYMBOLS = ['EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'EUR/CHF', 'AUD/USD', 'USD/CAD', 'NZD/USD', 'EUR/GBP',
               'EUR/JPY', 'GBP/JPY', 'CHF/JPY', 'GBP/CHF', 'EUR/AUD', 'EUR/CAD', 'AUD/CAD', 'AUD/JPY', 'CAD/JPY',
               'NZD/JPY', 'GBP/CAD', 'GBP/NZD', 'GBP/AUD', 'AUD/NZD', 'USD/SEK', 'EUR/SEK', 'EUR/NOK', 'USD/NOK',
               'USD/MXN', 'AUD/CHF', 'EUR/NZD', 'USD/ZAR', 'USD/HKD', 'ZAR/JPY', 'USD/TRY', 'EUR/TRY', 'NZD/CHF',
               'CAD/CHF', 'NZD/CAD', 'TRY/JPY', 'USD/CNH', 'AUS200', 'ESP35', 'FRA40', 'GER30', 'HKG33', 'JPN225',
               'NAS100', 'SPX500', 'UK100', 'US30', 'Copper', 'CHN50', 'EUSTX50', 'USDOLLAR', 'US2000', 'USOil',
               'UKOil', 'SOYF', 'NGAS', 'WHEATF', 'CORNF', 'Bund', 'XAU/USD', 'XAG/USD', 'BTC/USD', 'ETH/USD',
               'LTC/USD']


def get_fxcm_symbol(symbol):
    symbol = symbol.replace('_', '/').upper()
    if len(symbol) == 6:
        symbol = '%s/%s' % (symbol[:3], symbol[3:])

    if symbol in ALL_SYMBOLS:
        return symbol
    else:
        raise Exception('Invalid symbol for FXCM')


def get_fxcm_timeframe(timeframe):
    if timeframe in ['m1', 'm5', 'm15', 'm30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8',
                     'D1', 'W1', 'M1']:
        return timeframe
    timeframe_dict = {PERIOD_M1: 'm1', PERIOD_M5: 'm5', PERIOD_M15: 'm15', PERIOD_M30: 'm30', PERIOD_H1: 'H1',
                      PERIOD_H4: 'H4', PERIOD_D1: 'D1',
                      PERIOD_W1: 'W1', PERIOD_MN1: 'M1'}
    return timeframe_dict.get(timeframe)


SingletonFXCMAPI = SingletonDecorator(fxcmpy)

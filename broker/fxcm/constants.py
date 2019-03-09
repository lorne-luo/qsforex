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
    "logpath": "./logfile.txt",
    "_debugLevels": "Levels are (from most to least logging) DEBUG, INFO, WARNING, ERROR, CRITICAL",
    "debugLevel": "ERROR",
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
    symbol = symbol.replace('_', '/')
    if len(symbol) == 6:
        symbol = '%s/%s' % (symbol[:3], symbol[3:])

    if symbol in ALL_SYMBOLS:
        return symbol
    else:
        raise Exception('Invalid symbol for FXCM')

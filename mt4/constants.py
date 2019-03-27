from decimal import Decimal

from dateutil.relativedelta import relativedelta, MO

PERIOD_TICK = 0
PERIOD_M1 = 1
PERIOD_M5 = 5
PERIOD_M15 = 15
PERIOD_M30 = 30
PERIOD_H1 = 60
PERIOD_H4 = 240
PERIOD_D1 = 1440
PERIOD_W1 = 10080
PERIOD_MN1 = 43200
PERIOD_CHOICES = [PERIOD_M1, PERIOD_M5, PERIOD_M15, PERIOD_M30, PERIOD_H1, PERIOD_H4, PERIOD_D1, PERIOD_W1, PERIOD_MN1]


class OrderSide(object):
    BUY = 'BUY'
    SELL = 'SELL'


def get_timeframe_name(timeframe_value):
    if timeframe_value == PERIOD_M1:
        return 'M1'
    if timeframe_value == PERIOD_M5:
        return 'M5'
    if timeframe_value == PERIOD_M15:
        return 'M15'
    if timeframe_value == PERIOD_M30:
        return 'M30'
    if timeframe_value == PERIOD_H1:
        return 'H1'
    if timeframe_value == PERIOD_H4:
        return 'H4'
    if timeframe_value == PERIOD_D1:
        return 'D1'
    if timeframe_value == PERIOD_W1:
        return 'W1'
    if timeframe_value == PERIOD_MN1:
        return 'MN1'
    raise Exception('unsupport timeframe')


PIP_DICT = {
    # Currency
    'USDDKK': Decimal('0.0001'),
    'EURAUD': Decimal('0.0001'),
    'CHFJPY': Decimal('0.01'),
    'EURSGD': Decimal('0.0001'),
    'USDJPY': Decimal('0.01'),
    'EURTRY': Decimal('0.0001'),
    'USDCZK': Decimal('0.0001'),
    'GBPAUD': Decimal('0.0001'),
    'USDPLN': Decimal('0.0001'),
    'USDSGD': Decimal('0.0001'),
    'EURSEK': Decimal('0.0001'),
    'USDHKD': Decimal('0.0001'),
    'EURNZD': Decimal('0.0001'),
    'SGDJPY': Decimal('0.01'),
    'AUDCAD': Decimal('0.0001'),
    'GBPCHF': Decimal('0.0001'),
    'USDTHB': Decimal('0.01'),
    'TRYJPY': Decimal('0.01'),
    'CHFHKD': Decimal('0.0001'),
    'AUDUSD': Decimal('0.0001'),
    'EURDKK': Decimal('0.0001'),
    'EURUSD': Decimal('0.0001'),
    'AUDNZD': Decimal('0.0001'),
    'SGDHKD': Decimal('0.0001'),
    'EURHUF': Decimal('0.01'),
    'USDCNH': Decimal('0.0001'),
    'EURHKD': Decimal('0.0001'),
    'EURJPY': Decimal('0.01'),
    'NZDUSD': Decimal('0.0001'),
    'GBPPLN': Decimal('0.0001'),
    'GBPJPY': Decimal('0.01'),
    'USDTRY': Decimal('0.0001'),
    'EURCAD': Decimal('0.0001'),
    'USDSEK': Decimal('0.0001'),
    'GBPSGD': Decimal('0.0001'),
    'EURGBP': Decimal('0.0001'),
    'GBPHKD': Decimal('0.0001'),
    'USDZAR': Decimal('0.0001'),
    'AUDCHF': Decimal('0.0001'),
    'USDCHF': Decimal('0.0001'),
    'USDMXN': Decimal('0.0001'),
    'GBPUSD': Decimal('0.0001'),
    'EURCHF': Decimal('0.0001'),
    'EURNOK': Decimal('0.0001'),
    'AUDSGD': Decimal('0.0001'),
    'CADCHF': Decimal('0.0001'),
    'SGDCHF': Decimal('0.0001'),
    'CADHKD': Decimal('0.0001'),
    'USDINR': Decimal('0.01'),
    'NZDCAD': Decimal('0.0001'),
    'GBPZAR': Decimal('0.0001'),
    'NZDSGD': Decimal('0.0001'),
    'ZARJPY': Decimal('0.01'),
    'CADJPY': Decimal('0.01'),
    'GBPCAD': Decimal('0.0001'),
    'USDSAR': Decimal('0.0001'),
    'NZDCHF': Decimal('0.0001'),
    'NZDHKD': Decimal('0.0001'),
    'GBPNZD': Decimal('0.0001'),
    'AUDHKD': Decimal('0.0001'),
    'EURCZK': Decimal('0.0001'),
    'CHFZAR': Decimal('0.0001'),
    'USDHUF': Decimal('0.01'),
    'NZDJPY': Decimal('0.01'),
    'HKDJPY': Decimal('0.0001'),
    'CADSGD': Decimal('0.0001'),
    'USDNOK': Decimal('0.0001'),
    'USDCAD': Decimal('0.0001'),
    'AUDJPY': Decimal('0.01'),
    'EURPLN': Decimal('0.0001'),
    'EURZAR': Decimal('0.0001'),
    # METAL
    'XAUGBP': Decimal('0.01'),
    'XAGUSD': Decimal('0.0001'),
    'XAUNZD': Decimal('0.01'),
    'XAUXAG': Decimal('0.01'),
    'XAGJPY': Decimal('1'),
    'XAGHKD': Decimal('0.0001'),
    'XAGAUD': Decimal('0.0001'),
    'XAUCAD': Decimal('0.01'),
    'XAUAUD': Decimal('0.01'),
    'XAUJPY': Decimal('10'),
    'XAUHKD': Decimal('0.01'),
    'XPDUSD': Decimal('0.01'),
    'XAUUSD': Decimal('0.01'),
    'XAGCAD': Decimal('0.0001'),
    'XAUSGD': Decimal('0.01'),
    'XAGSGD': Decimal('0.0001'),
    'XAGEUR': Decimal('0.0001'),
    'XAGCHF': Decimal('0.0001'),
    'XPTUSD': Decimal('0.01'),
    'XAUCHF': Decimal('0.01'),
    'XAGNZD': Decimal('0.0001'),
    'XAGGBP': Decimal('0.0001'),
    'XAUEUR': Decimal('0.01'),
    # CFD
    'UK10YBGBP': Decimal('0.01'),
    'DE10YBEUR': Decimal('0.01'),
    'WTICOUSD': Decimal('0.01'),
    'BTCUSD': Decimal('1'),
    'NL25EUR': Decimal('0.01'),
    'CORNUSD': Decimal('0.01'),
    'SPX500USD': Decimal('1'),
    'JP225USD': Decimal('1'),
    'MBTCUSD': Decimal('0.01'),
    'USB02YUSD': Decimal('0.01'),
    'IN50USD': Decimal('1'),
    'TWIXUSD': Decimal('1'),
    'WHEATUSD': Decimal('0.01'),
    'HK33HKD': Decimal('1'),
    'US2000USD': Decimal('0.01'),
    'SUGARUSD': Decimal('0.0001'),
    'US30USD': Decimal('1'),
    'USB05YUSD': Decimal('0.01'),
    'NATGASUSD': Decimal('0.01'),
    'USB30YUSD': Decimal('0.01'),
    'SG30SGD': Decimal('0.1'),
    'AU200AUD': Decimal('1'),
    'CN50USD': Decimal('1'),
    'SOYBNUSD': Decimal('0.01'),
    'USB10YUSD': Decimal('0.01'),
    'EU50EUR': Decimal('1'),
    'FR40EUR': Decimal('1'),
    'BCOUSD': Decimal('0.01'),
    'NAS100USD': Decimal('1'),
    'DE30EUR': Decimal('1'),
    'XCUUSD': Decimal('0.0001'),
    'UK100GBP': Decimal('1'),
}


def get_mt4_symbol(symbol):
    symbol = str(symbol)
    return symbol.replace(' ', '').replace('_', '').replace('-', '').replace('/', '')


def pip_unit(symbol):
    symbol = get_mt4_symbol(symbol)
    if symbol not in PIP_DICT:
        raise Exception('%s not in PIP_DICT.')
    return PIP_DICT[symbol]


def pip(symbol, price=None, abs=False):
    symbol = get_mt4_symbol(symbol)
    if symbol not in PIP_DICT:
        raise Exception('%s not in PIP_DICT.' % symbol)

    pip_unit = PIP_DICT[symbol]
    if price:
        price = Decimal(str(price))
        return (price / pip_unit).quantize(Decimal("0.1"))
    if abs and pip_unit < 0:
        return pip_unit * -1
    return pip_unit


def profit_pip(symbol, open, close, side, abs=False):
    open = Decimal(str(open))
    close = Decimal(str(close))
    if side == OrderSide.BUY:
        profit = close - open
    else:
        profit = open - close

    return pip(symbol, profit)


def calculate_price(base_price, side, pip, instrument):
    instrument = get_mt4_symbol(instrument)
    pip_unit = pip(instrument)
    base_price = Decimal(str(base_price))
    pip = Decimal(str(pip))

    if side == OrderSide.BUY:
        return base_price + pip * pip_unit
    elif side == OrderSide.SELL:
        return base_price - pip * pip_unit


def get_candle_time(time, timeframe):
    t = time.replace(second=0, microsecond=0)

    if timeframe in [PERIOD_M1, PERIOD_M5, PERIOD_M15, PERIOD_M30]:
        minute = t.minute // timeframe * timeframe
        return t.replace(minute=minute)
    if timeframe in [PERIOD_H1, PERIOD_H4]:
        t = t.replace(minute=0)
        hourframe = int(timeframe / 60)
        hour = t.hour // hourframe * hourframe
        return t.replace(hour=hour)
    if timeframe in [PERIOD_D1]:
        return t.replace(hour=0, minute=0)
    if timeframe in [PERIOD_W1]:
        monday = time + relativedelta(weekday=MO(-1))
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)
    if timeframe in [PERIOD_MN1]:
        return t.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    raise NotImplementedError

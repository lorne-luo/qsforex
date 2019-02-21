from decimal import Decimal

from mt4.constants import OrderSide, PERIOD_M1, PERIOD_M5, PERIOD_M15, PERIOD_M30, PERIOD_H1, PERIOD_H4, PERIOD_D1, \
    PERIOD_W1, PERIOD_MN1


def get_symbol(symbol):
    '''MT4 symbol to Oanda V20 symbol name'''
    if '_' not in symbol:
        return symbol[:-3] + '_' + symbol[-3:]
    return symbol.upper()


def lots_to_units(lot, side):
    RATIO = 100000
    try:
        lot = Decimal(str(lot))
    except:
        return None

    if side == OrderSide.BUY:
        return lot * RATIO
    elif side == OrderSide.SELL:
        return lot * RATIO * -1
    raise Exception('Unknow direction.')


def get_timeframe_granularity(timeframe):
    if timeframe == PERIOD_M1:
        return 'M1'
    elif timeframe == PERIOD_M5:
        return 'M5'
    elif timeframe == PERIOD_M15:
        return 'M15'
    elif timeframe == PERIOD_M30:
        return 'M30'
    elif timeframe == PERIOD_H1:
        return 'H1'
    elif timeframe == PERIOD_H4:
        return 'H4'
    elif timeframe == PERIOD_D1:
        return 'D1'
    elif timeframe == PERIOD_W1:
        return 'W'
    elif timeframe == PERIOD_MN1:
        return 'M'
    return timeframe


def get_symbol(symbol):
    '''MT4 symbol to Oanda V20 symbol name'''
    if '_' not in symbol:
        return symbol[:-3] + '_' + symbol[-3:]
    return symbol.upper()



def lots_to_units(lot, side):
    RATIO = 100000
    if side == 'BUY':
        return lot * RATIO
    elif side == 'SELL':
        return lot * RATIO * -1
    raise Exception('Unknow direction.')

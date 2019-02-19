

def lots_to_units(lot, side):
    RATIO = 100000
    if side == 'BUY':
        return lot * RATIO
    elif side == 'BUY':
        return lot * RATIO * -1
    raise Exception('Unknow direction.')

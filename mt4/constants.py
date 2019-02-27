from dateutil.relativedelta import relativedelta, MO

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

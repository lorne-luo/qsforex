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
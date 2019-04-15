from datetime import datetime

from dateutil.relativedelta import relativedelta


def is_market_open():
    now = datetime.utcnow()

    close_hour = 19
    open_hour = 22

    HOLIDAY = [(1, 1)]
    if now.weekday() == 5:
        return False
    if now.weekday() == 4:
        return now.hour < close_hour
    if now.weekday() == 6:
        return now.hour > open_hour

    for date in HOLIDAY:
        next_day = now + relativedelta(hours=24)
        if (next_day.day, next_day.month) == date:
            return next_day.hour < close_hour

        if (now.day, now.month) == date:
            return now.hour > open_hour
    return True

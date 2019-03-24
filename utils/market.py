from datetime import datetime

from dateutil.relativedelta import relativedelta


def is_market_open():
    now = datetime.utcnow()
    HOLIDAY = [(1, 1)]
    if now.weekday() == 5:
        return False
    if now.weekday() == 4:
        return now.hour < 22
    if now.weekday() == 6:
        return now.hour > 22

    for date in HOLIDAY:
        next_day = now + relativedelta(hours=24)
        if (next_day.day, next_day.month) == date:
            return next_day.hour < 22

        if (now.day, now.month) == date:
            return now.hour > 22
    return True

from datetime import datetime


def is_market_open():
    now = datetime.utcnow()
    HOLIDAY = [(1, 1)]
    if now.weekday() == 5:
        return False
    if now.weekday() == 4:
        return now.hour < 20
    if now.weekday() == 6:
        return now.hour > 22

    for date in HOLIDAY:
        if (now.day, now.month) == date:
            return now.hour < 20 or now.hour > 22
    return True

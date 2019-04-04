import time
from datetime import datetime
from dateparser import parse


def parse_timestamp(timestamp, utc=False):
    if utc:
        return datetime.utcfromtimestamp(timestamp)
    else:
        return datetime.fromtimestamp(timestamp)


def datetime_to_timestamp(dt):
    return time.mktime(dt.timetuple())


def datetime_to_str(dt, format='%Y-%m-%d %H:%M:%S:%f'):
    if dt:
        return dt.strftime(format)
    return None


def str_to_datetime(string, format='%Y-%m-%d %H:%M:%S:%f'):
    if string:
        try:
            dt = datetime.strptime(string, format)
        except:
            dt = parse(string)

        return dt
    return None


def timestamp_to_str(timestamp, datetime_fmt="%Y/%m/%d %H:%M:%S:%f"):
    return datetime.fromtimestamp(timestamp).strftime(datetime_fmt)

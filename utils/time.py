from datetime import datetime
from dateparser import parse


def parse_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return dt


def datetime_to_str(dt, format='%Y-%m-%d %H:%M:%S:%f'):
    return dt.strftime(format)


def str_to_datetime(string, format='%Y-%m-%d %H:%M:%S:%f'):
    try:
        dt = datetime.strptime(string, format)
    except:
        dt = parse(string)

    return dt


def timestamp_to_str(timestamp, datetime_fmt="%Y/%m/%d %H:%M:%S:%f"):
    return datetime.fromtimestamp(timestamp).strftime(datetime_fmt)

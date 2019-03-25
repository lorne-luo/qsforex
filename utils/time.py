from datetime import datetime


def parse_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return dt


def datetime_to_str(dt, format='%Y-%m-%d %H:%M:%S:%f'):
    return dt.strftime(format)


def str_to_datetime(string, format='%Y-%m-%d %H:%M:%S:%f'):
    return datetime.strptime(string, format)


def timestamp_to_str(timestamp, datetime_fmt="%Y/%m/%d %H:%M:%S:%f"):
    return datetime.fromtimestamp(timestamp).strftime(datetime_fmt)

from datetime import datetime


def parse_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return dt


def datetime_to_str(dt):
    # datetime_format = "RFC3339",
    return dt.strftime('%Y-%m-%d %H:%M:%S:%f')

def timestamp_to_str(timestamp, datetime_fmt="%Y/%m/%d %H:%M:%S:%f"):
    return datetime.fromtimestamp(timestamp).strftime(datetime_fmt)
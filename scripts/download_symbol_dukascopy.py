import calendar
import copy
import lzma
from datetime import datetime as dt
from datetime import date, time
import datetime
import os, os.path
import sys
from pytz import timezone
import pytz
import urllib.request
from struct import *

import numpy as np
import pandas as pd

from qsforex import settings
from qsforex.utils.file import create_folder


def download_symbol_from_dukascopy(symbol, period):
    tdatetime = dt.strptime(period, '%Y%m')
    week, days = calendar.monthrange(tdatetime.year, tdatetime.month)
    y = tdatetime.year
    m = tdatetime.month
    for d in range(1, days + 1):
        for h in range(0, 24):
            dd = dt.combine(date(y, m, d), time(h, 0))
            currentdt = dt.now(pytz.utc)
            # Don't process future tickdata
            _dd = pytz.utc.localize(dd)
            if (_dd > currentdt):
                continue
            # Market opens 00:00-23:59 and Monday-Friday by EET, EST
            eet = pytz.utc.localize(dd).astimezone(pytz.timezone('Europe/Athens'))
            eet.replace(tzinfo=None)
            if (eet.isoweekday() >= 6):
                continue

            # download
            url = "http://www.dukascopy.com/datafeed/%s/%02d/%02d/%02d/%02dh_ticks.bi5" % (symbol, y, m - 1, d, h)
            file = os.path.join(settings.CSV_DATA_DIR, symbol, 'tick', str(y),
                                "%s_%02d_%02d_%02d_%02dh_ticks.bi5" % (symbol, y, m, d, h))
            create_folder(file)

            print("now downloading %s..." % url)
            try:
                urllib.request.urlretrieve(url, file)
            except Exception as ex:
                print("cannot find %s %s" % (url, str(ex)))
    # Download has been finished
    for d in range(1, days + 1):
        if (date(y, m, d).isoweekday() == 6):  # on UTC Saturday is always closed.
            continue
        outcsv = os.path.join(settings.CSV_DATA_DIR, symbol, 'tick', str(y),
                              "%s_%02d%02d%02d.csv" % (symbol, y, m, d))

        if os.path.isfile(outcsv):
            continue

        ff = open(outcsv, 'w')
        for h in range(0, 24):
            dd = dt.combine(date(y, m, d), time(h, 0))
            currentdt = dt.now(pytz.utc)
            # Don't process future tickdata
            _dd = pytz.utc.localize(dd)
            if (_dd > currentdt):
                ff.close()
                quit()

            # Market opens 00:00-23:59 and Monday-Friday by EET, EST
            eet = pytz.utc.localize(dd).astimezone(pytz.timezone('Europe/Athens'))
            eet.replace(tzinfo=None)
            if (eet.isoweekday() >= 6):
                continue

            file = os.path.join(settings.CSV_DATA_DIR, symbol, 'tick', str(y),
                                "%s_%02d_%02d_%02d_%02dh_ticks.bi5" % (symbol, y, m, d, h))
            try:
                f = open(file, "rb")
            except IOError:
                continue

            a = f.read()
            try:
                b = lzma.decompress(a)
            except:
                os.remove(file)
                continue
            os.remove(file)

            if (len(b) == 0):
                continue

            length = int(len(b) / 20)
            for _b in range(length):
                (__second, __ask, __bid, __askvol, __bidvol) = unpack('>IIIff', b[_b * 20:((_b + 1) * 20)])
                if 'ZARJPY' in symbol:
                    ask = float(__ask) / 100000
                    bid = float(__bid) / 100000
                elif 'JPY' in symbol:
                    ask = float(__ask) / 1000
                    bid = float(__bid) / 1000
                else:
                    ask = float(__ask) / 100000
                    bid = float(__bid) / 100000
                __time = dd + datetime.timedelta(0, float(__second) / 1000)
                _tstr = __time.strftime('%Y.%m.%d %H:%M:%S.%f')
                tstr = _tstr[0:23]
                _str = tstr + "," + str(bid) + "," + str(ask) + ",%.2f" % __bidvol + ",%.2f" % __askvol + "\n"
                ff.write(_str)
        ff.close()


# example:
# python scripts/download_symbol_dukascopy.py GBPUSD 201812

if __name__ == "__main__":
    print('DATA DIR:', settings.CSV_DATA_DIR)

    try:
        symbol = sys.argv[1]
        period = sys.argv[2]
    except IndexError:
        print("You need to enter a currency symbol, e.g. GBPUSD, and period YYYYMM as a command line parameter.")
    else:
        download_symbol_from_dukascopy(symbol, period)

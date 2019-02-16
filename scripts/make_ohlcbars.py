# -*- coding: utf-8 -*- 
# Copyright (c) 2015 NAKATA Maho All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

import calendar
import fileinput
import copy
import lzma
from datetime import datetime as dt
from datetime import date, time
import datetime
import os, os.path
import sys
from pytz import timezone
import pytz
import urllib
from struct import *
import io
import numpy as np
import pandas as pd

from qsforex import settings

if __name__ == "__main__":
    try:
        symbol = sys.argv[1]
        period = sys.argv[2]
    except IndexError:
        print("You need to enter a currency symbol, e.g. GBPUSD, and period YYYYMM as a command line parameter.")
    else:
        tdatetime = dt.strptime(period, '%Y%m')
        week, days = calendar.monthrange(tdatetime.year, tdatetime.month)
        y = tdatetime.year
        m = tdatetime.month

        ddd = dt.combine(date(y, m, 1), time(0, 0))
        eet = timezone('Europe/Athens').localize(ddd)
        back2utc = eet.astimezone(pytz.timezone('UTC'))
        yy = back2utc.year
        mm = back2utc.month
        dd = back2utc.day
        hh = back2utc.hour
        currentdt = dt.now(pytz.utc)
        # Don't process future tickdata
        _ddd = timezone('UTC').localize(dt.combine(date(yy, mm, dd), time(hh, 0)))
        if (_ddd > currentdt):
            quit()

        datadir = settings.CSV_DATA_DIR + "%s/1m/%02d" % (symbol, y)
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        datadir = settings.CSV_DATA_DIR + "%s/5m/%02d" % (symbol, y)
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        datadir = settings.CSV_DATA_DIR + "%s/15m/%02d" % (symbol, y)
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        datadir = settings.CSV_DATA_DIR + "%s/1h/%02d" % (symbol, y)
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        datadir = settings.CSV_DATA_DIR + "%s/4h/%02d" % (symbol, y)
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        datadir = settings.CSV_DATA_DIR + "%s/1d/%02d" % (symbol, y)
        if not os.path.exists(datadir):
            os.makedirs(datadir)

        for d in range(1, days + 1):
            if (date(y, m, d).isoweekday() >= 6):  # on ETC/EEST Saturday and Sunday are always closed.
                continue

            ddd = dt.combine(date(y, m, d), time(0, 0))
            eet = timezone('Europe/Athens').localize(ddd)
            back2utc = eet.astimezone(pytz.timezone('UTC'))
            yy = back2utc.year
            mm = back2utc.month
            dd = back2utc.day
            hh = back2utc.hour
            currentdt = dt.now(pytz.utc)
            # Don't process future tickdata
            _ddd = timezone('UTC').localize(dt.combine(date(yy, mm, dd), time(hh, 0)))
            if (_ddd > currentdt):
                continue

            file = os.path.join(settings.CSV_DATA_DIR, symbol, 'tick', str(y),
                                "%s_%02d%02d%02d.csv" % (symbol, y, m, d))
            print(file)
            # a = open(file).read()
            data = pd.read_csv(file, float_precision="high", header=None, parse_dates=True,
                               names=['timestamp', 'bid', 'ask', 'vol1', 'vol2'])
            p = data.iloc[0]
            _d = dt.combine(date(y, m, d), time(0, 0))
            p_first_row = pd.Series(
                [_d.strftime('%Y.%m.%d %H:%M:%S') + ".001", p['bid'], p['ask'], p['vol1'], p['vol2']],
                index=['timestamp', 'bid', 'ask', 'vol1', 'vol2'], name='-1')
            p = data.iloc[-1]
            _d = dt.combine(date(y, m, d), time(23, 59, 59))
            p_last_row = pd.Series(
                [_d.strftime('%Y.%m.%d %H:%M:%S') + ".999", p['bid'], p['ask'], p['vol1'], p['vol2']],
                index=['timestamp', 'bid', 'ask', 'vol1', 'vol2'], name=len(data))
            _data = data.append(p_last_row)
            alldata = _data.append(p_first_row)
            _all = alldata.sort_values(by=['timestamp'])

            idx = pd.to_datetime(_all['timestamp'])
            s_bid = pd.Series(_all.bid.values, index=idx)
            s_ask = pd.Series(_all.ask.values, index=idx)

            ohlc_bid1m = s_bid.resample("60s", how="ohlc", closed="right", label="right", fill_method="ffill",
                                        loffset="-60s")
            ohlc_ask1m = s_ask.resample("60s", how="ohlc", closed="right", label="right", fill_method="ffill",
                                        loffset="-60s")
            ohlc_bid1m['vol'] = pd.Series(0, index=ohlc_bid1m.index)
            ohlc_ask1m['vol'] = pd.Series(0, index=ohlc_ask1m.index)
            ohlc_bid1m_file = settings.CSV_DATA_DIR + "%s/1m/%02d/%s_%02d%02d%02d_bid1m.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_ask1m_file = settings.CSV_DATA_DIR + "%s/1m/%02d/%s_%02d%02d%02d_ask1m.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_bid1m.to_csv(ohlc_bid1m_file, date_format='%Y.%m.%d,%H:%M', header=False)
            ohlc_ask1m.to_csv(ohlc_ask1m_file, date_format='%Y.%m.%d,%H:%M', header=False)
            os.system("sed -i 's/\"//g' %s " % ohlc_bid1m_file)
            os.system("sed -i 's/\"//g' %s " % ohlc_ask1m_file)

            ohlc_bid5m = s_bid.resample("300s", how="ohlc", closed="right", label="right", loffset="-300s")
            ohlc_ask5m = s_ask.resample("300s", how="ohlc", closed="right", label="right", loffset="-300s")
            ohlc_bid5m['vol'] = pd.Series(0, index=ohlc_bid5m.index)
            ohlc_ask5m['vol'] = pd.Series(0, index=ohlc_ask5m.index)
            ohlc_bid5m_file = settings.CSV_DATA_DIR + "%s/5m/%02d/%s_%02d%02d%02d_bid5m.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_ask5m_file = settings.CSV_DATA_DIR + "%s/5m/%02d/%s_%02d%02d%02d_ask5m.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_bid5m.to_csv(ohlc_bid5m_file, date_format='%Y.%m.%d,%H:%M', header=False)
            ohlc_ask5m.to_csv(ohlc_ask5m_file, date_format='%Y.%m.%d,%H:%M', header=False)
            os.system("sed -i 's/\"//g' %s " % ohlc_bid5m_file)
            os.system("sed -i 's/\"//g' %s " % ohlc_ask5m_file)

            ohlc_bid15m = s_bid.resample("900s", how="ohlc", closed="right", label="right", loffset="-900s")
            ohlc_ask15m = s_ask.resample("900s", how="ohlc", closed="right", label="right", loffset="-900s")
            ohlc_bid15m['vol'] = pd.Series(0, index=ohlc_bid15m.index)
            ohlc_ask15m['vol'] = pd.Series(0, index=ohlc_ask15m.index)
            ohlc_bid15m_file = settings.CSV_DATA_DIR + "%s/15m/%02d/%s_%02d%02d%02d_bid15m.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_ask15m_file = settings.CSV_DATA_DIR + "%s/15m/%02d/%s_%02d%02d%02d_ask15m.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_bid15m.to_csv(ohlc_bid15m_file, date_format='%Y.%m.%d,%H:%M', header=False)
            ohlc_ask15m.to_csv(ohlc_ask15m_file, date_format='%Y.%m.%d,%H:%M', header=False)
            os.system("sed -i 's/\"//g' %s " % ohlc_bid15m_file)
            os.system("sed -i 's/\"//g' %s " % ohlc_ask15m_file)


            ohlc_bid30m = s_bid.resample("1800s", how="ohlc", closed="right", label="right", loffset="-1800s")
            ohlc_ask30m = s_ask.resample("1800s", how="ohlc", closed="right", label="right", loffset="-1800s")
            ohlc_bid30m['vol'] = pd.Series(0, index=ohlc_bid30m.index)
            ohlc_ask30m['vol'] = pd.Series(0, index=ohlc_ask30m.index)
            ohlc_bid30m_file = settings.CSV_DATA_DIR + "%s/30m/%02d/%s_%02d%02d%02d_bid15m.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_ask30m_file = settings.CSV_DATA_DIR + "%s/30m/%02d/%s_%02d%02d%02d_ask15m.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_bid30m.to_csv(ohlc_bid30m_file, date_format='%Y.%m.%d,%H:%M', header=False)
            ohlc_ask30m.to_csv(ohlc_ask30m_file, date_format='%Y.%m.%d,%H:%M', header=False)
            os.system("sed -i 's/\"//g' %s " % ohlc_bid30m_file)
            os.system("sed -i 's/\"//g' %s " % ohlc_ask30m_file)


            ohlc_bid1h = s_bid.resample("1h", how="ohlc", closed="right", label="right", fill_method="ffill",
                                        loffset="-1h")
            ohlc_ask1h = s_ask.resample("1h", how="ohlc", closed="right", label="right", fill_method="ffill",
                                        loffset="-1h")
            ohlc_bid1h['vol'] = pd.Series(0, index=ohlc_bid1h.index)
            ohlc_ask1h['vol'] = pd.Series(0, index=ohlc_ask1h.index)
            ohlc_bid1h_file = settings.CSV_DATA_DIR + "%s/1h/%02d/%s_%02d%02d%02d_bid1h.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_ask1h_file = settings.CSV_DATA_DIR + "%s/1h/%02d/%s_%02d%02d%02d_ask1h.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_bid1h.to_csv(ohlc_bid1h_file, date_format='%Y.%m.%d,%H:%M', header=False)
            ohlc_ask1h.to_csv(ohlc_ask1h_file, date_format='%Y.%m.%d,%H:%M', header=False)
            os.system("sed -i 's/\"//g' %s " % ohlc_bid1h_file)
            os.system("sed -i 's/\"//g' %s " % ohlc_ask1h_file)

            ohlc_bid4h = s_bid.resample("4h", how="ohlc", closed="right", label="right", fill_method="ffill",
                                        loffset="-4h")
            ohlc_ask4h = s_ask.resample("4h", how="ohlc", closed="right", label="right", fill_method="ffill",
                                        loffset="-4h")
            ohlc_bid4h['vol'] = pd.Series(0, index=ohlc_bid4h.index)
            ohlc_ask4h['vol'] = pd.Series(0, index=ohlc_ask4h.index)
            ohlc_bid4h_file = settings.CSV_DATA_DIR + "%s/4h/%02d/%s_%02d%02d%02d_bid4h.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_ask4h_file = settings.CSV_DATA_DIR + "%s/4h/%02d/%s_%02d%02d%02d_ask4h.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_bid4h.to_csv(ohlc_bid4h_file, date_format='%Y.%m.%d,%H:%M', header=False)
            ohlc_ask4h.to_csv(ohlc_ask4h_file, date_format='%Y.%m.%d,%H:%M', header=False)
            os.system("sed -i 's/\"//g' %s " % ohlc_bid4h_file)
            os.system("sed -i 's/\"//g' %s " % ohlc_ask4h_file)

            ohlc_bid1d = s_bid.resample("D", how="ohlc", closed="right", label="right", fill_method="ffill",
                                        loffset="-1d")
            ohlc_ask1d = s_ask.resample("D", how="ohlc", closed="right", label="right", fill_method="ffill",
                                        loffset="-1d")
            ohlc_bid1d['vol'] = pd.Series(0, index=ohlc_bid1d.index)
            ohlc_ask1d['vol'] = pd.Series(0, index=ohlc_ask1d.index)
            ohlc_bid1d_file = settings.CSV_DATA_DIR + "%s/1d/%02d/%s_%02d%02d%02d_bid1d.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_ask1d_file = settings.CSV_DATA_DIR + "%s/1d/%02d/%s_%02d%02d%02d_ask1d.csv" % (
            symbol, y, symbol, y, m, d)
            ohlc_bid1d.to_csv(ohlc_bid1d_file, date_format='%Y.%m.%d,%H:%M', header=False)
            ohlc_ask1d.to_csv(ohlc_ask1d_file, date_format='%Y.%m.%d,%H:%M', header=False)
            os.system("sed -i 's/\"//g' %s " % ohlc_bid1d_file)
            os.system("sed -i 's/\"//g' %s " % ohlc_ask1d_file)

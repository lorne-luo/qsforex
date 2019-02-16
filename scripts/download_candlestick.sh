CURRENCIES="EURUSD USDJPY GBPUSD AUDUSD NZDUSD USDCAD USDCHF"

#XAGUSD XAUUSD USDSGD USDNOK USDMXN USDZAR USDSEK CHFSGD AUDSGD NZDSGD
#SGDJPY EURNOK EURSEK EURSGD USDBRL USDCHN USDDKK USDHUF USDRUB USDTRY 
#USDPLN USDZAR USDHKD EURDKK EURMXN EURHUF EURTRY EURPLN EURZAR EURHKD
#EURSEK ZARJPY MXNJPY

YEARS="2018 2017 2016 2015 2014 2013 2012 2011 2010"
MONTHS="12 11 10 09 08 07 06 05 04 03 02 01"

for year in $YEARS ; do
    for month in $MONTHS ; do
        for currency in $CURRENCIES ; do
            sem --jobs 8 "python scripts/download_symbol_dukascopy_eet.py $currency $year$month; python scripts/make_ohlcbars.py $currency $year$month"  ";" echo done
        done
        sem --wait 
    done
done


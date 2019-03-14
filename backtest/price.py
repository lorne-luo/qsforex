from datetime import datetime

import time
from decimal import Decimal
import pandas as pd
import requests
from socketIO_client import SocketIO

from strategy import TickEvent


class HistoricCSVPriceHandler(object):
    """
    HistoricCSVPriceHandler is designed to read tick data
    for each requested currency pair and stream those
    to the provided events queue.
    """

    def __init__(self, pairs, time, token, events_queue):
        """
        Initialises the historic data handler by requesting
        the location of the CSV files and a list of symbols.

        It will be assumed that all files are of the form
        'pair.csv', where "pair" is the currency pair. For
        GBP/USD the filename is GBPUSD.csv.
        """
        self.pairs = pairs
        self.events_queue = events_queue
        self.prices = self.set_up_prices_dict()
        self.continue_backtest = True
        self.cur_date_indx = 0
        self.TRADING_API_URL = 'https://api-demo.fxcm.com:443'
        self.WEBSOCKET_PORT = 443
        self.ACCESS_TOKEN = token
        self.bearer_access_token = ""
        self.offerID = {'EUR/USD': 1, 'USD/JPY': 2, 'GBP/USD': 3, 'USD/CHF': 4, 'EUR/CHF': 5, 'AUD/USD': 6,
                        'USD/CAD': 7, 'NZD/USD': 8, 'EUR/GBP': 9, 'EUR/JPY': 10, 'GBP/JPY': 11, 'CHF/JPY': 12,
                        'GBP/CHF': 13, 'EUR/AUD': 14, 'EUR/CAD': 15, 'AUD/CAD': 16, 'AUD/JPY': 17, 'CAD/JPY': 18,
                        'NZD/JPY': 19, 'GBP/CAD': 20, 'GBP/NZD': 21, 'GBP/AUD': 22, 'AUD/NZD': 28, 'USD/SEK': 30,
                        'EUR/SEK': 32, 'EUR/NOK': 36, 'USD/NOK': 37, 'USD/MXN': 38, 'AUD/CHF': 39, 'EUR/NZD': 40,
                        'USD/ZAR': 47, 'USD/HKD': 50, 'ZAR/JPY': 71, 'USD/TRY': 83, 'EUR/TRY': 87, 'NZD/CHF': 89,
                        'CAD/CHF': 90, 'TRY/JPY': 98, 'USD/CNH': 105, 'USDOLLAR': 1058}
        self.periodID = time
        self.socketIO = None
        self.df_data = self.set_up_df

    # SocketIO definitions
    def on_error(self, ws, error):
        print(error)

    def on_close(self):
        print('Websocket closed.')

    def on_connect(self):
        print('Websocket connected: ' + self.socketIO._engineIO_session.id)

    # End of SocketIO definitions

    def request_processor(self, method, params):
        """ Trading server request help function. """

        headers = {
            'User-Agent': 'request',
            'Authorization': self.bearer_access_token,
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        rresp = requests.get(self.TRADING_API_URL + method, headers=headers, params=params)
        if rresp.status_code == 200:
            data = rresp.json()
            if data["response"]["executed"] is True:
                return True, data
            return False, data["response"]["error"]
        else:
            return False, rresp.status_code

    def post_request_processor(self, method, params):
        """ Trading server request help function. """

        headers = {
            'User-Agent': 'request',
            'Authorization': self.bearer_access_token,
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        rresp = requests.post(self.TRADING_API_URL + method, headers=headers, data=params)
        if rresp.status_code == 200:
            data = rresp.json()
            if data["response"]["executed"] is True:
                return True, data
            return False, data["response"]["error"]
        else:
            return False, rresp.status_code

    def create_bearer_token(self, t, s):
        bt = "Bearer " + s + t
        return bt

    def set_up_prices_dict(self):
        price_dict = dict(
            (k, v) for k, v in [
                (p, {"bid": None, "ask": None, "time": None}) for p in self.pairs
            ]
        )
        return price_dict

    @property
    def set_up_df(self):
        self.socketIO = SocketIO(self.TRADING_API_URL, self.WEBSOCKET_PORT, params={'access_token': self.ACCESS_TOKEN})
        self.socketIO.on('connect', self.on_connect)
        self.socketIO.on('disconnect', self.on_close)
        self.bearer_access_token = self.create_bearer_token(self.ACCESS_TOKEN, self.socketIO._engineIO_session.id)

        df_dict = []
        for pair in self.pairs:
            hist_status, hist_response = self.request_processor(
                '/candles/' + str(self.offerID[pair]) + '/' + self.periodID, {
                    'num': 1000,
                    'to': time.mktime(datetime.now().timetuple())
                    # 'to': 1503835200
                })
            if hist_status is True:
                hist_data = hist_response['candles']
                df = pd.DataFrame(hist_data)
                df.columns = ["time", "bidopen", "bidclose", "bidhigh", "bidlow", "askopen", "askclose", "askhigh",
                              "asklow", "TickQty"]
                print("Data Retrieved %s: length=%s" % (pair, len(hist_data)))
                df_dict.append(df)
            else:
                print("No Data Retrieved... " + hist_response)
                exit(0)
        return df_dict

    def stream_next_tick(self):
        """
        The Backtester has now moved over to a single-threaded
        model in order to fully reproduce results on each run.
        This means that the stream_to_queue method is unable to
        be used and a replacement, called stream_next_tick, is
        used instead.

        This method is called by the backtesting function outside
        of this class and places a single tick onto the queue, as
        well as updating the current bid/ask and inverse bid/ask.
        """
        for index in range(len(self.df_data)):
            end = len(self.df_data[index])
            if (self.cur_date_indx < end):
                row = self.df_data[index][self.cur_date_indx:(self.cur_date_indx + 1)]
                bid = Decimal(str(row["bidopen"][self.cur_date_indx])).quantize(Decimal("0.00001"))
                ask = Decimal(str(row["askopen"][self.cur_date_indx])).quantize(Decimal("0.00001"))
                time = row["time"][self.cur_date_indx]
                # Create decimalised prices for traded pair
                self.prices[self.pairs[index]]["bid"] = bid
                self.prices[self.pairs[index]]["ask"] = ask
                self.prices[self.pairs[index]]["time"] = time
                # Create the tick event for the queue
                tev = TickEvent(self.pairs[index], time, bid, ask)
                tev.open = Decimal(str(row["askopen"][self.cur_date_indx])).quantize(Decimal("0.00001"))
                tev.high = Decimal(str(row["askhigh"][self.cur_date_indx])).quantize(Decimal("0.00001"))
                tev.low = Decimal(str(row["bidlow"][self.cur_date_indx])).quantize(Decimal("0.00001"))
                tev.close = Decimal(str(row["bidclose"][self.cur_date_indx])).quantize(Decimal("0.00001"))
                self.events_queue.put(tev)
            else:
                self.continue_backtest = False
                return
        self.cur_date_indx += 1

import logging
from datetime import datetime

try:
    import Queue as queue
except ImportError:
    import queue
import time

from strategy import PortfolioAllocation, RSIStrategy
from portfolio import Portfolio
from price import HistoricCSVPriceHandler


class Backtest(object):
    """
    Enscapsulates the settings and components for carrying out
    an event-driven backtest on the foreign exchange markets.
    """

    def __init__(
            self, pairs, period, token, data_handler, strategy,
            strategy_params, portfolio, equity=10000.0,
            heartbeat=0.0, max_iters=10000000000
    ):
        """
        Initialises the backtest.
        """
        self.pairs = pairs
        self.time = period
        self.token = token
        self.events = queue.Queue()
        self.ticker = data_handler(self.pairs, self.time, self.token, self.events)
        self.strategy_params = strategy_params
        self.strategy = strategy(
            self.pairs, self.events, **self.strategy_params
        )
        self.initial = equity
        self.equity = equity
        self.heartbeat = heartbeat
        self.max_iters = max_iters
        self.portfolio = portfolio(self.ticker, self.events, backtest=True, equity=self.equity)
        print('Equity=%s' % self.portfolio.equity)

    def _run_backtest(self):
        """
        Carries out an infinite while loop that polls the
        events queue and directs each event to either the
        strategy component of the execution handler. The
        loop will then pause for "heartbeat" seconds and
        continue unti the maximum number of iterations is
        exceeded.
        """
        print("Running Backtest...")
        iters = 0
        signal_count = 0
        while iters < self.max_iters and self.ticker.continue_backtest:
            try:
                event = self.events.get(False)
            except queue.Empty:
                self.ticker.stream_next_tick()
            else:
                if event is not None:
                    if event.type == 'TICK':
                        # print(event)
                        self.strategy.calculate_signals(event)
                        self.portfolio.update_portfolio(event)
                    elif event.type == 'SIGNAL':
                        # print('[%s] %s' % (
                        # datetime.utcfromtimestamp(event.time).strftime('%Y-%m-%d %H:%M'), event.__dict__))
                        signal_count = signal_count + 1
                        self.portfolio.execute_signal(event)
                    elif event.type == 'ORDER':
                        # print(event.__dict__)
                        pass
            time.sleep(self.heartbeat)
            iters += 1
        else:
            for pair in self.pairs:
                self.portfolio.close_position(pair)

        # print("Signal Sent: %d" % signal_count)
        print("Closed Trades: %d" % self.portfolio.trade_count)
        print("win Executed: %d" % self.portfolio.win_count)
        print("loss Executed: %d" % self.portfolio.loss_count)
        print("Win rate: %0.2f%% vs %0.2f%%" % (self.portfolio.get_win_rate(), self.portfolio.get_loss_rate()))
        print('Initial Equity: %s' % self.initial)
        print("Portfolio Balance: %0.2f" % self.portfolio.balance)
        print("Profit: %0.2f" % (self.portfolio.balance - self.initial))
        percentage = (self.portfolio.balance / self.initial - 1) * 100
        print("Portfolio Profit: %0.2f" % percentage + '%')


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(filename='backtest.log', level=logging.INFO, filemode='w+')
    logger = logging.getLogger('RestMeanReversion.backtest.log')

    fxcm_token = "8a1e87908a70362782ea9744e2c9c82689bde3ac"
    # Enter the pair(s) you would like to trade as a list
    # Pick from {'EUR/USD','USD/JPY','GBP/USD','USD/CHF','EUR/CHF','AUD/USD','USD/CAD','NZD/USD',
    #           'EUR/GBP','EUR/JPY','GBP/JPY','CHF/JPY','GBP/CHF','EUR/AUD','EUR/CAD','AUD/CAD',
    #           'AUD/JPY','CAD/JPY','NZD/JPY','GBP/CAD','GBP/NZD','GBP/AUD','AUD/NZD','USD/SEK',
    #           'EUR/SEK','EUR/NOK','USD/NOK','USD/MXN','AUD/CHF','EUR/NZD','USD/ZAR','USD/HKD',
    #           'ZAR/JPY','USD/TRY','EUR/TRY','NZD/CHF','CAD/CHF','TRY/JPY','USD/CNH','USDOLLAR'}
    pairs = ["EUR/USD"]
    # Enter the time period you would like
    # Pick from {'m1','m5','m15','m30','H1','H2','H3','H4','H6','H8','D1','W1','M1'}
    period = 'H1'
    # Create the strategy parameters if necessary
    strategy_params = {
        "equity": 10000,
        "pair_targets": [40, 30]
    }
    strategy_params2 = {
        'window': 14
    }
    # Create and execute the backtest
    backtest = Backtest(
        pairs, period, fxcm_token, HistoricCSVPriceHandler, RSIStrategy,
        strategy_params2, Portfolio
    )
    backtest._run_backtest()

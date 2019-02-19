from __future__ import print_function

from qsforex.backtest.backtest import Backtest
from qsforex.execution.execution import SimulatedExecution
from qsforex.portfolio.portfolio import Portfolio
from qsforex import settings
from qsforex.strategy.strategy import MovingAverageCrossStrategy
from qsforex.pricing.price import HistoricCSVPriceHandler

if __name__ == "__main__":
    pairs = ["GBPUSD"]

    # Create the strategy parameters for the
    # MovingAverageCrossStrategy
    strategy_params = {
        "short_window": 500,
        "long_window": 2000
    }

    # Create and execute the backtest
    backtest = Backtest(
        pairs, HistoricCSVPriceHandler,
        MovingAverageCrossStrategy, strategy_params,
        Portfolio, SimulatedExecution,
        equity=settings.EQUITY,
        startday=20181202, endday=20181203,
        base_currency=settings.BASE_CURRENCY
    )
    backtest.simulate_trading()

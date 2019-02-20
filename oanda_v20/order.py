import logging
from decimal import Decimal, ROUND_HALF_UP

from oanda_v20.api import api
from oanda_v20.common.view import print_entity
from oanda_v20.convertor import get_symbol, lots_to_units
from qsforex.oanda_v20.constants import TransactionName, OrderType, OrderPositionFill, TimeInForce
from qsforex import settings

logger = logging.getLogger(__name__)


def create_market_order(instrument, side, lots=0.1, type=OrderType.MARKET, timeInForce=TimeInForce.FOK,
                        priceBound=None, positionFill=OrderPositionFill.DEFAULT, clientExtensions=None,
                        takeProfitOnFill=None, stopLossOnFill=None, trailingStopLossOnFill=None,
                        tradeClientExtensions=None):
    instrument = get_symbol(instrument)

    units = lots_to_units(lots, side)
    response = api.order.market(
        settings.ACCOUNT_ID,
        instrument=instrument, units=str(units), type=type, timeInForce=timeInForce,
        priceBound=priceBound, positionFill=positionFill, clientExtensions=None,
        takeProfitOnFill=takeProfitOnFill, stopLossOnFill=stopLossOnFill, trailingStopLossOnFill=trailingStopLossOnFill,
        tradeClientExtensions=tradeClientExtensions
    )

    if response.status >= 200:
        transactions = []
        for name in TransactionName.all():
            try:
                transaction = response.get(name, None)
                transactions.append(transaction)
            except:
                pass
        for t in transactions:
            print_entity(t, title=t.__class__.__name__)
            print('')
        return transactions
    else:
        logger.error(
            "[Market_order] {}, {}, {}\n".format(
                response.status,
                response.body.get('errorCode'),
                response.body.get('errorMessage'),
            )
        )
        return False, response.body.get('errorMessage')

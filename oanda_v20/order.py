import logging
from decimal import Decimal, ROUND_HALF_UP

from v20.transaction import StopLossDetails, ClientExtensions, TakeProfitDetails, TrailingStopLossDetails

from oanda_v20.api import api
from oanda_v20.common.view import print_entity
from oanda_v20.convertor import get_symbol, lots_to_units
from qsforex.oanda_v20.constants import TransactionName, OrderType, OrderPositionFill, TimeInForce
from qsforex import settings

logger = logging.getLogger(__name__)


def create_market_order(instrument, side, lots=0.1, type=OrderType.MARKET, timeInForce=TimeInForce.FOK,
                        priceBound=None, positionFill=OrderPositionFill.DEFAULT,
                        takeProfitOnFill=None, stopLossOnFill=None, trailingStopLossOnFill=None,
                        client_id=None, client_tag=None, client_comment=None):
    instrument = get_symbol(instrument)
    units = lots_to_units(lots, side)


    if stopLossOnFill:
        stopLossOnFill = StopLossDetails(price=str(stopLossOnFill))

    if takeProfitOnFill:
        takeProfitOnFill = TakeProfitDetails(price=str(takeProfitOnFill))

    if trailingStopLossOnFill:
        trailingStopLossOnFill = TrailingStopLossDetails(distance=str(trailingStopLossOnFill))

    # client extension
    client_args = {'id': client_id, 'tag': client_tag, 'comment': client_comment}
    if any(client_args.values()):
        tradeClientExtensions = ClientExtensions(**client_args)
    else:
        tradeClientExtensions = None

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

        #todo fail: ORDER_CANCEL,MARKET_ORDER_REJECT
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


# from oanda_v20.order import *
# response=create_market_order('EUR_USD','BUY',stopLossOnFill='1.3145',client_tag='test',client_comment='test')

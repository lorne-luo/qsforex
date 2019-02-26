import logging
from decimal import Decimal, ROUND_HALF_UP

from mt4.constants import OrderSide
from oanda_v20.common.convertor import get_symbol

from v20.transaction import StopLossDetails, ClientExtensions, TakeProfitDetails, TrailingStopLossDetails
from oanda_v20.base import api, EntityBase
from oanda_v20.common.logger import log_error
from oanda_v20.common.prints import print_orders
from oanda_v20.common.view import print_entity, print_response_entity, price_to_string, heartbeat_to_string
from oanda_v20.common.convertor import get_symbol, lots_to_units
from oanda_v20.common.constants import TransactionName, OrderType, OrderPositionFill, TimeInForce, OrderTriggerCondition
import settings

logger = logging.getLogger(__name__)


class PriceMixin(EntityBase):
    _prices = {}

    def _process_price(self,price):
        instrument = price.instrument
        time = price.time
        bid = Decimal(str(price.bids[0].price))
        ask = Decimal(str(price.asks[0].price))
        spread = self.get_pips(ask - bid, instrument)
        self._prices[instrument] = {'time': time, 'bid': bid, 'ask': ask, 'spread': spread}
    # list
    def list_prices(self, instruments=None, since=None, includeUnitsAvailable=True):
        instruments = instruments or self.DEFAULT_CURRENCIES
        response = self.api.pricing.get(
            self.account_id,
            instruments=",".join(instruments),
            since=since,
            includeUnitsAvailable=includeUnitsAvailable
        )

        prices = response.get("prices", 200)
        for price in prices:
            if settings.DEBUG:
                print(price_to_string(price))
            self._process_price(price)

        return self._prices

    def streaming(self, instruments=None, snapshot=True):
        instruments = instruments or self.DEFAULT_CURRENCIES
        # print(",".join(instruments))
        # print(self.account_id)

        response = self.stream_api.pricing.stream(
            self.account_id,
            instruments=",".join(instruments),
            snapshot=snapshot,
        )

        for msg_type, msg in response.parts():
            if msg_type == "pricing.PricingHeartbeat" and settings.DEBUG:
                print(msg_type, heartbeat_to_string(msg))
            elif msg_type == "pricing.ClientPrice" and msg.type == 'PRICE':
                self._process_price(msg)
                print(price_to_string(msg))
            else:
                print('Unknow type:', msg_type, msg.__dict__)

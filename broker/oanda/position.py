import logging
from decimal import Decimal, ROUND_HALF_UP

from broker.oanda.base import EntityBase
from broker.oanda.common.logger import log_error
from broker.oanda.common.convertor import get_symbol

logger = logging.getLogger(__name__)


class PositionMixin(EntityBase):

    def pull_position(self, instrument):
        """pull position by instrument"""
        instrument = get_symbol(instrument)
        response = self.api.position.get(self.account_id, instrument)

        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'QEURY_POSITION')
            return False, response.body['errorMessage']

        last_transaction_id = response.get('lastTransactionID', 200)
        position = response.get('position', 200)
        if position:
            self.positions[position.instrument] = position

        return True, position


    def list_all_positions(self):
        response = self.api.position.list(
            self.account_id,
        )

        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'LIST_ALL_POSITION')
            return False, response.body['errorMessage']

        last_transaction_id = response.get('lastTransactionID', 200)
        positions = response.get('positions', 200)
        for position in positions:
            self.positions[position.instrument] = position

        return True, positions


    def list_open_positions(self):
        response = self.api.position.list_open(
            self.account_id,
        )

        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'LIST_OPEN_POSITION')
            return False, response.body['errorMessage']

        last_transaction_id = response.get('lastTransactionID', 200)
        positions = response.get('positions', 200)
        for position in positions:
            self.positions[position.instrument] = position
        return True, positions


    def close_all_position(self):
        instruments = self.positions.keys()
        logger.error('[CLOSE_ALL_POSITIONS] Start.')
        for i in instruments:
            self.close_position(i, 'ALL', 'ALL')

    def close_position(self, instrument, longUnits='ALL', shortUnits='ALL'):
        instrument = get_symbol(instrument)

        response = self.api.position.close(
            self.account_id,
            instrument,
            longUnits=longUnits,
            shortUnits=shortUnits
        )

        if response.status < 200 or response.status > 299:
            log_error(logger, response, 'CLOSE_POSITION')
            return False, response.body['errorMessage']

        longOrderCreateTransaction = response.get('longOrderCreateTransaction', None)
        longOrderFillTransaction = response.get('longOrderFillTransaction', None)
        longOrderCancelTransaction = response.get('longOrderCancelTransaction', None)
        shortOrderCreateTransaction = response.get('shortOrderCreateTransaction', None)
        shortOrderFillTransaction = response.get('shortOrderFillTransaction', None)
        shortOrderCancelTransaction = response.get('shortOrderCancelTransaction', None)
        relatedTransactionIDs = response.get('relatedTransactionIDs', None)
        lastTransactionID = response.get('lastTransactionID', None)
        print(longOrderCreateTransaction.__dict__)
        print(longOrderFillTransaction.__dict__)
        print(longOrderCancelTransaction.__dict__)
        print(shortOrderCreateTransaction.__dict__)
        print(shortOrderFillTransaction.__dict__)
        print(shortOrderCancelTransaction.__dict__)
        print(relatedTransactionIDs.__dict__)
        print(lastTransactionID)
        return True, 'done'


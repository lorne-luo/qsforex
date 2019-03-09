import logging
from decimal import Decimal, ROUND_HALF_UP

from broker.base import PositionBase
from broker.fxcm.constants import get_fxcm_symbol

logger = logging.getLogger(__name__)


class PositionMixin(PositionBase):
    positions = {}

    @property
    def open_positions(self):
        return self.fxcmpy.open_pos

    @property
    def closed_positions(self):
        return self.fxcmpy.closed_pos

    def pull_position(self, instrument):
        return

    def list_all_positions(self):
        return True, self.fxcmpy.open_pos + self.fxcmpy.closed_pos

    def list_open_positions(self):
        return True, self.fxcmpy.open_pos

    def close_all_position(self):
        self.fxcmpy.close_all()

    def close_position(self, instrument, longUnits='ALL', shortUnits='ALL'):
        instrument = get_fxcm_symbol(instrument)
        self.fxcmpy.close_all_for_symbol(instrument)

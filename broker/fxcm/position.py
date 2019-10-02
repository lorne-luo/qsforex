import logging

from broker.base import PositionBase
from broker.fxcm.constants import get_fxcm_symbol

logger = logging.getLogger(__name__)


class PositionMixin(PositionBase):
    positions = {}

    @property
    def open_positions(self):
        return self.fxcmpy.get_open_positions()

    @property
    def closed_positions(self):
        return self.fxcmpy.get_closed_positions()

    def pull_position(self, instrument):
        return self.open_positions()

    def list_all_positions(self):
        data = {}
        for k, v in self.fxcmpy.open_pos.items():
            data[k] = v
        for k, v in self.fxcmpy.closed_pos.items():
            data[k] = v

        return data

    def list_open_positions(self):
        return self.fxcmpy.get_open_positions()

    def close_all_position(self):
        self.fxcmpy.close_all()

    def close_position(self, instrument, longUnits='ALL', shortUnits='ALL'):
        instrument = get_fxcm_symbol(instrument)
        self.fxcmpy.close_all_for_symbol(instrument)

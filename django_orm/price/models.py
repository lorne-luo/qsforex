from django.db import models
from django.utils.translation import ugettext_lazy as _


class OHLCBase(models.Model):
    timeframe = models.IntegerField(_('timeframe'), blank=True, null=True)
    open = models.DecimalField(_('price'), max_digits=8, decimal_places=5)
    high = models.DecimalField(_('price'), max_digits=8, decimal_places=5)
    low = models.DecimalField(_('price'), max_digits=8, decimal_places=5)
    close = models.DecimalField(_('price'), max_digits=8, decimal_places=5)
    volume = models.DecimalField(_('price'), max_digits=8, decimal_places=2)

    class Meta:
        abstract = True


class EURUSD(OHLCBase):
    pass


class USDJPY(OHLCBase):
    pass


class GBPUSD(OHLCBase):
    pass


class USDCHF(OHLCBase):
    pass


class USDCAD(OHLCBase):
    pass


class AUDUSD(OHLCBase):
    pass


class NZDUSD(OHLCBase):
    pass


class XAUUSD(OHLCBase):
    pass

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Page(models.Model):
    title = models.CharField(_('name'), max_length=254, null=False, blank=False)
    url = models.URLField(_('url'), null=False, blank=False)
    price = models.DecimalField(_('price'), max_digits=8, decimal_places=2)
    original_price = models.DecimalField(_('original price'), max_digits=8, decimal_places=2)

    class Meta:
        verbose_name_plural = _('Page')
        verbose_name = _('Page')

    def __str__(self):
        return '%s' % self.title

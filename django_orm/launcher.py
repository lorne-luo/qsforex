import sys
import os

import django

base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
sys.path.append(base_dir)

import django_orm.configs as qsforex_settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.conf import settings

settings.configure(DATABASES=qsforex_settings.DATABASES, INSTALLED_APPS=qsforex_settings.INSTALLED_APPS)
django.setup()

from django_orm.trade.models import Trade

orders = Trade.objects.all()
print(orders.count())

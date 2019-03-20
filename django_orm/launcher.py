import os

import django

import settings as my_settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.conf import settings

settings.configure(DATABASES=my_settings.DATABASES, INSTALLED_APPS=('django_orm.store',))
django.setup()

from django_orm.store.models import Page

orders = Page.objects.all()
print(orders.count())

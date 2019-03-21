import os
import sys

base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
sys.path.append(base_dir)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'qsforex',
        'USER': 'qsforex',
        'PASSWORD': 'qsforex',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
SECRET_KEY = 'test_secret'

INSTALLED_APPS = [
    'django_orm.trade',
    'django_orm.price',
]

try:
    from django_orm.local import *
except ImportError:
    pass

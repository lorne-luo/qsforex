import v20
import settings


def create_api_context():
    """
    Initialize an API context based on the Config instance
    """
    ctx = v20.Context(
        hostname=settings.API_DOMAIN,
        application=settings.APPLICATION_NAME,
        token=settings.ACCESS_TOKEN,
    )

    return ctx


def create_streaming_context():
    """
    Initialize a streaming API context based on the Config instance
    """
    ctx = v20.Context(
        hostname=settings.STREAM_DOMAIN,
        application=settings.APPLICATION_NAME,
        token=settings.ACCESS_TOKEN,
        datetime_format='RFC3339'
    )

    return ctx


class SingletonDecorator:
    def __init__(self, klass):
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwds):
        if self.instance == None:
            self.instance = self.klass(*args, **kwds)
        return self.instance


SingletonAPIContext = SingletonDecorator(v20.Context)
SingletonStreamAPIContext = SingletonDecorator(v20.Context)

api = SingletonAPIContext(hostname=settings.API_DOMAIN,
                       application=settings.APPLICATION_NAME,
                       token=settings.ACCESS_TOKEN, )

stream_api = SingletonStreamAPIContext(hostname=settings.STREAM_DOMAIN,
                              application=settings.APPLICATION_NAME,
                              token=settings.ACCESS_TOKEN,
                              datetime_format='RFC3339')


class EntityBase(object):
    api = api
    stream_api = stream_api
    account_id = None

    _instruments = {}
    order_states = {}
    positions = {}
    transactions = []
    trades = {}
    orders = {}
    details = None

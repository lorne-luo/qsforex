import v20
from qsforex import settings


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


SingletonContext = SingletonDecorator(v20.Context)

api = SingletonContext(hostname=settings.API_DOMAIN,
                       application=settings.APPLICATION_NAME,
                       token=settings.ACCESS_TOKEN, )

stream_api = SingletonContext(hostname=settings.STREAM_DOMAIN,
                              application=settings.APPLICATION_NAME,
                              token=settings.ACCESS_TOKEN, )


class EntityBase(object):
    api = api
    account_id = None

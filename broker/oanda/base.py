import v20
import settings
from utils.singleton import SingletonDecorator


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


SingletonAPIContext = SingletonDecorator(v20.Context)

api = SingletonAPIContext(hostname=settings.API_DOMAIN,
                          application=settings.APPLICATION_NAME,
                          token=settings.ACCESS_TOKEN)

stream_api = SingletonAPIContext(hostname=settings.STREAM_DOMAIN,
                                 application=settings.APPLICATION_NAME,
                                 token=settings.ACCESS_TOKEN)


class OANDABase(object):
    api = None
    stream_api = None
    account_id = None

    _instruments = {}
    order_states = {}
    positions = {}
    transactions = []
    trades = {}
    orders = {}
    details = None
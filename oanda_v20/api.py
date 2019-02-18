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
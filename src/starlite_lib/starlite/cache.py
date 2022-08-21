from starlite import CacheConfig
from starlite.config.cache import default_cache_key_builder
from starlite.connection import Request

from starlite_lib.config import api_settings, app_settings
from starlite_lib.redis import redis


def cache_key_builder(request: Request) -> str:
    """
    App name prefixed cache key builder.

    Parameters
    ----------
    request : Request
        Current request instance.

    Returns
    -------
    str
        App slug prefixed cache key.
    """
    return f"{app_settings.slug}:{default_cache_key_builder(request)}"


config = CacheConfig(
    backend=redis,
    expiration=api_settings.CACHE_EXPIRATION,
    cache_key_builder=cache_key_builder,
)
"""Cache configuration for application."""

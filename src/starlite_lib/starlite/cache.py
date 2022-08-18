from collections.abc import Awaitable
from typing import Any

from starlite import CacheConfig
from starlite.config import CacheBackendProtocol, default_cache_key_builder
from starlite.connection import Request

from starlite_lib.config import api_settings, app_settings
from starlite_lib.redis import redis


class RedisAsyncioBackend(CacheBackendProtocol):  # pragma: no cover
    async def get(self, key: str) -> Awaitable[Any]:
        """
        Retrieve a valued from cache corresponding to the given key
        """
        return await redis.get(key)  # type:ignore[return-value]

    async def set(self, key: str, value: Any, expiration: int) -> Awaitable[Any]:
        """
        Set a value in cache for a given key with a given expiration in seconds
        """
        return await redis.set(key, value, expiration)  # type:ignore[return-value]

    async def delete(self, key: str) -> Awaitable[Any]:
        """
        Remove a value from the cache for a given key
        """
        return await redis.delete(key)  # type:ignore[return-value]


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
    backend=RedisAsyncioBackend(),
    expiration=api_settings.CACHE_EXPIRATION,
    cache_key_builder=cache_key_builder,
)
"""Cache configuration for application."""

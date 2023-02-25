"""Application cache config."""
from __future__ import annotations

from typing import TYPE_CHECKING

from starlite import CacheConfig
from starlite.cache.redis_cache_backend import (
    RedisCacheBackend,
    RedisCacheBackendConfig,
)
from starlite.config.cache import default_cache_key_builder

from starlite_saqlalchemy import settings

if TYPE_CHECKING:
    from typing import Any

    from starlite.connection import Request


def cache_key_builder(request: Request[Any, Any]) -> str:
    """Cache key builder.

    Args:
        request: Current request instance.

    Returns:
        App slug prefixed cache key.
    """
    return f"{settings.app.slug}:{default_cache_key_builder(request)}"


backend_config = RedisCacheBackendConfig(
    url=settings.redis.URL,
    port=settings.redis.PORT,
    db=settings.redis.DB,
)

config = CacheConfig(
    backend=RedisCacheBackend(config=backend_config),
    expiration=settings.api.CACHE_EXPIRATION,
    cache_key_builder=cache_key_builder,
)
"""Cache configuration for application."""

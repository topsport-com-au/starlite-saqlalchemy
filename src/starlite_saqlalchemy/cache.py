"""Application cache config."""
from __future__ import annotations

from typing import TYPE_CHECKING

from starlite import CacheConfig
from starlite.config.cache import default_cache_key_builder

from starlite_saqlalchemy import redis, settings

if TYPE_CHECKING:
    from typing import Any

    from starlite.connection import Request


def cache_key_builder(request: Request[Any, Any]) -> str:
    """
    Args:
        request: Current request instance.

    Returns:
        App slug prefixed cache key.
    """
    return f"{settings.app.slug}:{default_cache_key_builder(request)}"


config = CacheConfig(
    backend=redis.client,  # pyright:ignore[reportGeneralTypeIssues]
    expiration=settings.api.CACHE_EXPIRATION,
    cache_key_builder=cache_key_builder,
)
"""Cache configuration for application."""

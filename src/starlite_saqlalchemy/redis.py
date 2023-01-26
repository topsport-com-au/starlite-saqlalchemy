"""Application redis instance."""
from __future__ import annotations

from redis.asyncio import Redis

from starlite_saqlalchemy import settings

__all__ = ["client"]

client: Redis[bytes] = Redis.from_url(
    settings.redis.URL,
    socket_connect_timeout=settings.redis.SOCKET_CONNECT_TIMEOUT,
    health_check_interval=settings.redis.HEALTH_CHECK_INTERVAL,
    socket_keepalive=settings.redis.SOCKET_KEEPALIVE,
)
"""Async [`Redis`][redis.Redis] instance.

Configure via [CacheSettings][starlite_saqlalchemy.settings.RedisSettings].
"""

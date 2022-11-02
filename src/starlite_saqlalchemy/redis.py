"""Application redis instance."""
from __future__ import annotations

from redis.asyncio import Redis

from starlite_saqlalchemy import settings

__all__ = ["client"]

client: Redis[bytes] = Redis.from_url(settings.redis.URL)
"""
Async [`Redis`][redis.Redis] instance, configure via
[CacheSettings][starlite_saqlalchemy.settings.RedisSettings].
"""

"""Application redis instance."""

from redis.asyncio import Redis

from . import settings

__all__ = ["client"]

client = Redis.from_url(settings.redis.URL)
"""
Async [`Redis`][redis.Redis] instance, configure via
[CacheSettings][starlite_saqlalchemy.settings.RedisSettings].
"""

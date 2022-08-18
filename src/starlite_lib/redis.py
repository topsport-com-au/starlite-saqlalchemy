from redis.asyncio import Redis

from .config import cache_settings

__all__ = ["redis"]

redis = Redis.from_url(cache_settings.URL)
"""
Async [`Redis`][redis.Redis] instance, configure via 
[CacheSettings][starlite_lib.config.CacheSettings].
"""

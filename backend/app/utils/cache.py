import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None


def get_redis_connection() -> Optional[aioredis.Redis]:
    """Return a shared async Redis client, or None if Redis is unavailable."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
            )
        except Exception as e:
            logger.warning("Failed to create Redis connection: %s", e)
            return None
    return _redis_client


async def cache_get(key: str) -> Optional[str]:
    """Get from cache. Returns None silently if Redis unavailable."""
    try:
        redis = get_redis_connection()
        if redis is None:
            return None
        return await redis.get(key)
    except Exception as e:
        logger.warning("Cache GET failed for key %s: %s", key, e)
        return None


async def cache_set(key: str, value: str, ttl: int = 300) -> bool:
    """Set in cache. Returns False silently if Redis unavailable."""
    try:
        redis = get_redis_connection()
        if redis is None:
            return False
        await redis.setex(key, ttl, value)
        return True
    except Exception as e:
        logger.warning("Cache SET failed for key %s: %s", key, e)
        return False


async def cache_delete(key: str) -> bool:
    """Delete a single cache key. Returns False silently if Redis unavailable."""
    try:
        redis = get_redis_connection()
        if redis is None:
            return False
        await redis.delete(key)
        return True
    except Exception as e:
        logger.warning("Cache DELETE failed for key %s: %s", key, e)
        return False


async def cache_delete_pattern(pattern: str) -> int:
    """Delete all cache keys matching a glob pattern using SCAN (not KEYS).
    Returns the number of keys deleted, or -1 if Redis unavailable."""
    try:
        redis = get_redis_connection()
        if redis is None:
            return -1
        deleted = 0
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                await redis.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        return deleted
    except Exception as e:
        logger.warning("Cache DELETE PATTERN failed for pattern %s: %s", pattern, e)
        return -1

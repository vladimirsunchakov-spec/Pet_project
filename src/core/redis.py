import json
from typing import Any, Optional, Type
import redis.asyncio as redis
import logging
import redis.asyncio as redis
from healthcheck.router import healthcheck
from src.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def initialize(self) -> bool:
        try:
            self._client = await redis.from_url(
                settings.redis_url,
                decode_responses=True,
                max_connections = 20,
                retry_on_timeout=True,
                socket_keepalive=True,
                health_check_interval=30,
            )
            await self._client.ping()
            logger.info("Redis client initialize successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self._client = None
            return False

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            logger.info("Redis client closed")

    async def _ensure_client(self) -> redis.Redis:
        if not self._client:
            raise RuntimeError("Redis client not initialized. Call initialize() first.")
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        try:
            client = await self._ensure_client()
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis GET error for '{key}': {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) ->bool:
        try:
            client = await self._ensure_client()
            if ttl is None:
                ttl = settings.cache_ttl_seconds
            serialized = json.dumps(value)
            if ttl <= 0:
                await client.set(key, serialized)
            else:
                await client.setex(key,ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for '{key}': {e}")
            return False

    async def delete(self, key: str) -> int:
        try:
            client = await self._ensure_client()
            return await client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE error for '{key}': {e}")
            return 0

    async def exists(self, key: str) -> bool:
        try:
            client = await self._ensure_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for '{key}': {e}")
            return False

    async def ping(self) -> bool:
        try:
            client = await self._ensure_client()
            return await client.ping()
        except Exception:
            return False

    async def get_cached(self, key: str, model_class: Type) -> Optional[Any]:
        try:
            data = await self.get(key)
            if data:
                logger.debug(f"Cache HIT: {key}")
                return model_class.model_validate_json(data)
            logger.debug(f"Cache MISS: {key}")
        except Exception as e:
            logger.warning(f"Redis get_cached error for '{key}': {e}")
        return None

    async def set_cached(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        try:
            if ttl is None:
                ttl = settings.cache_ttl_seconds
            result = await self.set(key, data.model_dump(), ttl=ttl)
            if result:
                logger.debug(f"Cache SET: {key}")
            return result
        except Exception as e:
            logger.warning(f"Redis set_cached error for '{key}': {e}")
            return False

    async def invalidate(self, key: str) -> None:
        try:
            await self.delete(key)
            logger.info(f"Cache invalidated: {key}")
        except Exception as e:
            logger.warning(f"Redis invalidate error for '{key}': {e}")

    async def invalidate_pattern(self, pattern: str) -> None:
        try:
            client = await self._ensure_client()
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
                logger.info(f"Cache invalidated {len(keys)} keys with pattern {pattern}")
        except Exception as e:
            logger.warning(f"Redis invalidate_pattern error for '{pattern}': {e}")

redis_client = RedisClient()

import json
from typing import Any, Optional, Type
import logging
import redis.asyncio as redis
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
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                health_check_interval=30,
            )
            await self._client.ping()
            logger.info("Redis client initialized successfully")
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
            data = await self._client.get(key)
            if data:
                logger.debug(f"Cache HIT: {key}")
                return model_class.model_validate_json(data)
            logger.debug(f"Cache MISS: {key}")
        except Exception as e:
            logger.warning(f"Redis get_cached error for '{key}': {e}")
        return None

    async def get_cached(self, key: str, model_class: Type) -> Optional[Any]:
        try:
            client = await self._ensure_client()
            data = await client.get(key)
            if data:
                logger.debug(f"Cache HIT: {key}")
                return model_class.model_validate_json(data)
            logger.debug(f"Cache MISS: {key}")
        except Exception as e:
            logger.warning(f"Redis get_cached error for '{key}': {e}")
        return None

    async def set_cached(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        try:
            client = await self._ensure_client()
            if ttl is None:
                ttl = settings.cache_ttl_seconds
            serialized = json.dumps(data.model_dump)

            if ttl <= 0:
                await self._client.set(key, serialized)
            else:
                await self._client.setex(key, serialized)
            logger.debug(f"Cache SET: {key}")
            return True
        except Exception as e:
            logger.warning(f"Redis set_cached error for '{key}': {e}")
            return False

    async def invalidate(self, key: str) -> None:
        try:
            client = await self._ensure_client()
            await client.delete(key)
            logger.info(f"Cache invalidated: {key}")
        except Exception as e:
            logger.warning(f"Redis invalidate error for '{key}': {e}")

redis_client = RedisClient()

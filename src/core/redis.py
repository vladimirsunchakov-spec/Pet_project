import json
from typing import Any, Optional
import redis.asyncio as redis
from src.config import settings

class RedisClient:
    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def initialize(self):
        self._client = await redis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections = 20
        )

    async def close(self):
        if self._client:
            await self._client.close()

    async def get(self, key: str) -> Optional[Any]:
        data = await self._client.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        if ttl is None:
            ttl = settings.cache_ttl_seconds
        await self._client.setex(key,ttl, json.dumps(value))

    async def delete(self, key: str):
        await self._client.delete(key)

redis_client = RedisClient()

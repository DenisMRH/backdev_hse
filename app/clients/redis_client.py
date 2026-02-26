import os
import logging
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisClient:
    _instance = None
    _client: Redis | None = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> None:
        if self._client is None:
            url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._client = Redis.from_url(url, decode_responses=True)
            try:
                await self._client.ping()
            except Exception:
                self._client = None
                raise
            logger.info("Redis client connected")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Redis client closed")

    def is_connected(self) -> bool:
        return self._client is not None

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("Redis client is not initialized")
        return self._client

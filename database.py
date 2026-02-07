import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
import os

logger = logging.getLogger(__name__)


class Database:
    _instance = None
    _pool: asyncpg.Pool = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self):
        if self._pool is None:
            conn_string = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5433/ads_db"
            )
            self._pool = await asyncpg.create_pool(conn_string, min_size=1, max_size=10)
            logger.info("Database pool created")
    
    async def close(self):
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        
        async with self._pool.acquire() as connection:
            yield connection

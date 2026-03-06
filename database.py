import asyncpg
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional
import logging
import os
import time

logger = logging.getLogger(__name__)

from app.metrics import DB_QUERY_DURATION_SECONDS


def _query_type(sql: Any) -> Optional[str]:
    if not isinstance(sql, str):
        return None
    head = sql.lstrip().split(None, 1)
    if not head:
        return None
    verb = head[0].lower()
    if verb in {"select", "insert", "update", "delete"}:
        return verb
    return None


class _InstrumentedConnection:
    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def fetchrow(self, query: str, *args, **kwargs):
        qt = _query_type(query)
        start = time.perf_counter()
        try:
            return await self._conn.fetchrow(query, *args, **kwargs)
        finally:
            if qt is not None:
                DB_QUERY_DURATION_SECONDS.labels(query_type=qt).observe(time.perf_counter() - start)

    async def fetch(self, query: str, *args, **kwargs):
        qt = _query_type(query)
        start = time.perf_counter()
        try:
            return await self._conn.fetch(query, *args, **kwargs)
        finally:
            if qt is not None:
                DB_QUERY_DURATION_SECONDS.labels(query_type=qt).observe(time.perf_counter() - start)

    async def execute(self, query: str, *args, **kwargs):
        qt = _query_type(query)
        start = time.perf_counter()
        try:
            return await self._conn.execute(query, *args, **kwargs)
        finally:
            if qt is not None:
                DB_QUERY_DURATION_SECONDS.labels(query_type=qt).observe(time.perf_counter() - start)

    def __getattr__(self, name: str):
        return getattr(self._conn, name)


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
                "postgresql://postgres:postgres@localhost:5434/ads_db"
            )
            safe_url = conn_string.split("@")[-1] if "@" in conn_string else "?"
            logger.info("Database connecting to %s", safe_url)
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
            yield _InstrumentedConnection(connection)

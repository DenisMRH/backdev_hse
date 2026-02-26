import pytest
from app.clients.redis_client import RedisClient


@pytest.fixture
async def redis_client():
    client = RedisClient()
    try:
        await client.connect()
        yield client
    finally:
        await client.close()
        RedisClient._instance = None
        RedisClient._client = None

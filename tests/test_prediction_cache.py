import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from storages.prediction_cache import PredictionCacheStorage
from app.clients.redis_client import RedisClient


@pytest.mark.asyncio
async def test_predict_by_id_returns_cached_result_when_available(monkeypatch):
    cache = PredictionCacheStorage()
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value='{"is_violation": true, "probability": 0.9}')
    monkeypatch.setattr(cache.redis, "is_connected", lambda: True)
    monkeypatch.setattr(cache.redis, "_client", mock_client)

    result = await cache.get_prediction_by_ad(1)

    assert result == (True, 0.9)
    mock_client.get.assert_called_once_with("prediction:ad:1")


@pytest.mark.asyncio
async def test_predict_by_id_returns_none_when_cache_miss(monkeypatch):
    cache = PredictionCacheStorage()
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=None)
    monkeypatch.setattr(cache.redis, "is_connected", lambda: True)
    monkeypatch.setattr(cache.redis, "_client", mock_client)

    result = await cache.get_prediction_by_ad(1)

    assert result is None


@pytest.mark.asyncio
async def test_set_prediction_by_ad_calls_redis_with_correct_args(monkeypatch):
    cache = PredictionCacheStorage()
    mock_client = MagicMock()
    mock_setex = AsyncMock()
    mock_client.setex = mock_setex
    monkeypatch.setattr(cache.redis, "is_connected", lambda: True)
    monkeypatch.setattr(cache.redis, "_client", mock_client)

    await cache.set_prediction_by_ad(1, False, 0.15)

    mock_setex.assert_called_once()
    call_args = mock_setex.call_args
    assert call_args[0][0] == "prediction:ad:1"
    assert call_args[0][1] == 3600
    assert '"is_violation": false' in call_args[0][2]
    assert '"probability": 0.15' in call_args[0][2]


@pytest.mark.asyncio
async def test_items_service_uses_cache_before_db(monkeypatch):
    from services.items import ItemsService

    service = ItemsService()
    cached_result = (True, 0.85)
    monkeypatch.setattr(
        service.cache,
        "get_prediction_by_ad",
        AsyncMock(return_value=cached_result),
    )

    result = await service.predict_by_id(1)

    assert result == cached_result
    service.cache.get_prediction_by_ad.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_items_service_sets_cache_on_miss(monkeypatch):
    from models.domain import AdvertisementWithUser
    from services.items import ItemsService
    from services import ml_model

    service = ItemsService()
    ad = AdvertisementWithUser(
        id=1,
        user_id=1,
        name="Test",
        description="Desc",
        category=1,
        images_qty=5,
        is_verified_seller=True,
    )
    monkeypatch.setattr(service.cache, "get_prediction_by_ad", AsyncMock(return_value=None))
    monkeypatch.setattr(service.ad_repository, "get_with_user", AsyncMock(return_value=ad))
    monkeypatch.setattr(service.cache, "set_prediction_by_ad", AsyncMock())
    monkeypatch.setattr(ml_model, "get_prediction", lambda f: (False, 0.1))

    await service.predict_by_id(1)

    service.cache.set_prediction_by_ad.assert_called_once()
    call_args = service.cache.set_prediction_by_ad.call_args[0]
    assert call_args[0] == 1
    assert isinstance(call_args[1], bool)
    assert isinstance(call_args[2], float)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_prediction_cache_storage_set_and_get(redis_client):
    storage = PredictionCacheStorage()

    await storage.set_prediction_by_ad(100, True, 0.77)
    result = await storage.get_prediction_by_ad(100)

    assert result == (True, 0.77)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_prediction_cache_storage_delete(redis_client):
    storage = PredictionCacheStorage()

    await storage.set_prediction_by_ad(200, False, 0.2)
    await storage.delete_prediction_by_ad(200)
    result = await storage.get_prediction_by_ad(200)

    assert result is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_moderation_result_cache_set_and_get(redis_client):
    storage = PredictionCacheStorage()

    await storage.set_moderation_result(50, {"task_id": 50, "status": "completed", "is_violation": True, "probability": 0.9})
    result = await storage.get_moderation_result(50)

    assert result is not None
    assert result["task_id"] == 50
    assert result["status"] == "completed"
    assert result["is_violation"] is True
    assert result["probability"] == 0.9


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_moderation_results_by_task_ids(redis_client):
    storage = PredictionCacheStorage()

    await storage.set_moderation_result(1, {"task_id": 1})
    await storage.set_moderation_result(2, {"task_id": 2})
    await storage.delete_moderation_results_by_task_ids([1, 2])

    assert await storage.get_moderation_result(1) is None
    assert await storage.get_moderation_result(2) is None

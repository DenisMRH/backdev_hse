import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from main import app
from services.ml_model import ModelClient
from repositories.advertisements import AdvertisementRepository
from repositories.users import UserRepository
from repositories.moderation_results import ModerationResultRepository
from models.domain import (
    UserCreate,
    AdvertisementCreate,
    User,
    Advertisement,
    AdvertisementWithUser,
    ModerationResult,
)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(ModelClient, "_instance", None)
    
    with TestClient(app) as c:
        yield c
    
    monkeypatch.setattr(ModelClient, "_instance", None)


@pytest.mark.parametrize("advertisement_id,expected_status", [
    (-1, 422),
    (0, 422),
    (-999, 422),
])
def test_simple_predict_invalid_ids(client, advertisement_id, expected_status):
    response = client.post("/simple_predict", json={"advertisement_id": advertisement_id})
    assert response.status_code == expected_status


@pytest.mark.parametrize("is_verified,images_qty,expected_violation", [
    (True, 5, False),
    (False, 1, True),
    (True, 10, False),
    (False, 0, True),
])
def test_predict_parametrized(client, is_verified, images_qty, expected_violation):
    payload = {
        "seller_id": 1,
        "is_verified_seller": is_verified,
        "item_id": 100,
        "name": "Test Item",
        "description": "Test description",
        "category": 1,
        "images_qty": images_qty
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_violation"] == expected_violation
    assert isinstance(data["probability"], float)
    assert 0 <= data["probability"] <= 1


@pytest.mark.parametrize(
    "name,description,expected_status",
    [
        ("", "Valid description", 200),
        ("Valid name", "", 200),
        ("Name", "A" * 5000, 200),
        ("A" * 1000, "Description", 200),
    ],
    ids=["empty_name", "empty_desc", "long_desc", "long_name"],
)
def test_predict_edge_cases_parametrized(client, name, description, expected_status):
    payload = {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 100,
        "name": name,
        "description": description,
        "category": 1,
        "images_qty": 5
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == expected_status


def test_create_user_in_db(monkeypatch):
    mock_user = User(id=1, is_verified=True)
    
    async def mock_create(self, user_data):
        return User(id=1, is_verified=user_data.is_verified)
    
    async def mock_get_by_id(self, user_id):
        if user_id == 1:
            return mock_user
        return None
    
    async def mock_delete(self, user_id):
        return user_id == 1
    
    monkeypatch.setattr(UserRepository, "create", mock_create)
    monkeypatch.setattr(UserRepository, "get_by_id", mock_get_by_id)
    monkeypatch.setattr(UserRepository, "delete", mock_delete)
    
    import asyncio
    user_repo = UserRepository()
    user_data = UserCreate(is_verified=True)
    created_user = asyncio.run(user_repo.create(user_data))
    
    assert created_user.id == 1
    assert created_user.is_verified is True
    
    fetched = asyncio.run(user_repo.get_by_id(1))
    assert fetched is not None
    assert fetched.id == created_user.id
    
    deleted = asyncio.run(user_repo.delete(1))
    assert deleted is True


def test_create_advertisement_in_db(monkeypatch):
    mock_user = User(id=1, is_verified=True)
    mock_ad = Advertisement(
        id=1,
        user_id=1,
        name="Test Advertisement",
        description="This is a test advertisement",
        category=1,
        images_qty=5
    )
    
    async def mock_create_user(self, user_data):
        return mock_user
    
    async def mock_create_ad(self, ad_data):
        return Advertisement(
            id=1,
            user_id=ad_data.user_id,
            name=ad_data.name,
            description=ad_data.description,
            category=ad_data.category,
            images_qty=ad_data.images_qty
        )
    
    async def mock_get_by_id(self, ad_id):
        if ad_id == 1:
            return mock_ad
        return None
    
    monkeypatch.setattr(UserRepository, "create", mock_create_user)
    monkeypatch.setattr(AdvertisementRepository, "create", mock_create_ad)
    monkeypatch.setattr(AdvertisementRepository, "get_by_id", mock_get_by_id)
    
    import asyncio
    user_repo = UserRepository()
    ad_repo = AdvertisementRepository()
    
    user_data = UserCreate(is_verified=True)
    created_user = asyncio.run(user_repo.create(user_data))
    
    ad_data = AdvertisementCreate(
        user_id=created_user.id,
        name="Test Advertisement",
        description="This is a test advertisement",
        category=1,
        images_qty=5
    )
    created_ad = asyncio.run(ad_repo.create(ad_data))
    
    assert created_ad.id == 1
    assert created_ad.user_id == 1
    assert created_ad.name == "Test Advertisement"
    assert created_ad.description == "This is a test advertisement"
    assert created_ad.category == 1
    assert created_ad.images_qty == 5
    
    fetched = asyncio.run(ad_repo.get_by_id(1))
    assert fetched is not None
    assert fetched.name == "Test Advertisement"


def test_get_advertisement_with_user_from_db(monkeypatch):
    mock_ad_with_user = AdvertisementWithUser(
        id=1,
        user_id=1,
        name="Test Ad with User",
        description="Testing JOIN query",
        category=2,
        images_qty=3,
        is_verified_seller=True
    )
    
    async def mock_get_with_user(self, ad_id):
        if ad_id == 1:
            return mock_ad_with_user
        return None
    
    monkeypatch.setattr(AdvertisementRepository, "get_with_user", mock_get_with_user)
    
    import asyncio
    ad_repo = AdvertisementRepository()
    ad_with_user = asyncio.run(ad_repo.get_with_user(1))
    
    assert ad_with_user is not None
    assert ad_with_user.id == 1
    assert ad_with_user.user_id == 1
    assert ad_with_user.is_verified_seller is True
    assert ad_with_user.name == "Test Ad with User"


def test_predict_verified_seller(client):
    payload = {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 100,
        "name": "Test Item",
        "description": "Description",
        "category": 1,
        "images_qty": 5
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "is_violation" in data
    assert "probability" in data
    assert data["is_violation"] is False
    assert isinstance(data["probability"], float)
    assert 0 <= data["probability"] <= 1


def test_predict_violation_case(client):
    payload = {
        "seller_id": 2,
        "is_verified_seller": False,
        "item_id": 101,
        "name": "Test Item 2",
        "description": "Description 2",
        "category": 2,
        "images_qty": 1
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "is_violation" in data
    assert "probability" in data
    assert data["is_violation"] is True
    assert isinstance(data["probability"], float)
    assert 0 <= data["probability"] <= 1


def test_simple_predict_missing_id(client):
    response = client.post("/simple_predict", json={})
    assert response.status_code == 422


def test_simple_predict_advertisement_not_found(client, monkeypatch):
    async def mock_get_with_user(self, ad_id):
        return None

    monkeypatch.setattr(AdvertisementRepository, "get_with_user", mock_get_with_user)

    response = client.post("/simple_predict", json={"advertisement_id": 99999})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_async_predict_creates_task(client, monkeypatch):
    mock_ad = Advertisement(
        id=1, user_id=1, name="A", description="B", category=1, images_qty=5
    )

    async def mock_get_by_id(self, ad_id):
        return mock_ad if ad_id == 1 else None

    monkeypatch.setattr(AdvertisementRepository, "get_by_id", mock_get_by_id)

    created = ModerationResult(
        id=123,
        item_id=1,
        status="pending",
        is_violation=None,
        probability=None,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        processed_at=None,
    )

    async def mock_create_pending(self, item_id):
        return created

    monkeypatch.setattr(ModerationResultRepository, "create_pending", mock_create_pending)

    mock_kafka = MagicMock()
    mock_kafka.send_moderation_request = AsyncMock(return_value=None)
    client.app.state.kafka = mock_kafka

    response = client.post("/async_predict", json={"item_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == 123
    assert data["status"] == "pending"
    assert "Moderation request accepted" in data["message"]
    mock_kafka.send_moderation_request.assert_called_once_with(1, 123)


def test_async_predict_accepts_any_item_id(client, monkeypatch):
    created = ModerationResult(
        id=456,
        item_id=99999,
        status="pending",
        is_violation=None,
        probability=None,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        processed_at=None,
    )

    async def mock_create_pending(self, item_id):
        return created

    monkeypatch.setattr(ModerationResultRepository, "create_pending", mock_create_pending)
    kafka = MagicMock()
    kafka.send_moderation_request = AsyncMock()
    client.app.state.kafka = kafka

    response = client.post("/async_predict", json={"item_id": 99999})
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == 456
    kafka.send_moderation_request.assert_called_once_with(99999, 456)


def test_async_predict_kafka_unavailable(client, monkeypatch):
    client.app.state.kafka = None

    response = client.post("/async_predict", json={"item_id": 1})
    assert response.status_code == 503
    assert "Kafka" in response.json()["detail"]


def test_async_predict_kafka_send_failure_marks_task_failed(client, monkeypatch):
    created = ModerationResult(
        id=777,
        item_id=1,
        status="pending",
        is_violation=None,
        probability=None,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        processed_at=None,
    )

    async def mock_create_pending(self, item_id):
        return created

    failed_calls = []

    async def mock_set_failed(self, task_id, error_message):
        failed_calls.append((task_id, error_message))

    monkeypatch.setattr(ModerationResultRepository, "create_pending", mock_create_pending)
    monkeypatch.setattr(ModerationResultRepository, "set_failed", mock_set_failed)

    kafka = MagicMock()
    kafka.send_moderation_request = AsyncMock(side_effect=RuntimeError("kafka down"))
    client.app.state.kafka = kafka

    response = client.post("/async_predict", json={"item_id": 1})
    assert response.status_code == 503
    assert "Failed to send" in response.json()["detail"]
    assert len(failed_calls) == 1
    assert failed_calls[0][0] == 777


def test_moderation_result_pending(client, monkeypatch):
    from storages.prediction_cache import PredictionCacheStorage

    result = ModerationResult(
        id=10,
        item_id=1,
        status="pending",
        is_violation=None,
        probability=None,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        processed_at=None,
    )

    async def mock_get_by_id(self, task_id):
        return result if task_id == 10 else None

    monkeypatch.setattr(ModerationResultRepository, "get_by_id", mock_get_by_id)
    monkeypatch.setattr(PredictionCacheStorage, "get_moderation_result", AsyncMock(return_value=None))

    response = client.get("/moderation_result/10")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == 10
    assert data["status"] == "pending"
    assert data["is_violation"] is None
    assert data["probability"] is None


def test_moderation_result_completed(client, monkeypatch):
    from storages.prediction_cache import PredictionCacheStorage

    result = ModerationResult(
        id=20,
        item_id=2,
        status="completed",
        is_violation=True,
        probability=0.87,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        processed_at=datetime.now(timezone.utc),
    )

    async def mock_get_by_id(self, task_id):
        return result if task_id == 20 else None

    monkeypatch.setattr(ModerationResultRepository, "get_by_id", mock_get_by_id)
    monkeypatch.setattr(PredictionCacheStorage, "get_moderation_result", AsyncMock(return_value=None))
    monkeypatch.setattr(PredictionCacheStorage, "set_moderation_result", AsyncMock())

    response = client.get("/moderation_result/20")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == 20
    assert data["status"] == "completed"
    assert data["is_violation"] is True
    assert data["probability"] == 0.87


def test_moderation_result_not_found(client, monkeypatch):
    from storages.prediction_cache import PredictionCacheStorage

    async def mock_get_by_id(self, task_id):
        return None

    monkeypatch.setattr(ModerationResultRepository, "get_by_id", mock_get_by_id)
    monkeypatch.setattr(PredictionCacheStorage, "get_moderation_result", AsyncMock(return_value=None))

    response = client.get("/moderation_result/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_moderation_result_failed_includes_error(client, monkeypatch):
    from storages.prediction_cache import PredictionCacheStorage

    result = ModerationResult(
        id=30,
        item_id=3,
        status="failed",
        is_violation=None,
        probability=None,
        error_message="Advertisement not found",
        created_at=datetime.now(timezone.utc),
        processed_at=datetime.now(timezone.utc),
    )

    async def mock_get_by_id(self, task_id):
        return result if task_id == 30 else None

    monkeypatch.setattr(ModerationResultRepository, "get_by_id", mock_get_by_id)
    monkeypatch.setattr(PredictionCacheStorage, "get_moderation_result", AsyncMock(return_value=None))

    response = client.get("/moderation_result/30")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error_message"] == "Advertisement not found"


def test_close_advertisement_not_found(client, monkeypatch):
    async def mock_get_by_id(self, ad_id):
        return None

    monkeypatch.setattr(AdvertisementRepository, "get_by_id", mock_get_by_id)

    response = client.post("/close", json={"item_id": 99999})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_close_advertisement_success(client, monkeypatch):
    from storages.prediction_cache import PredictionCacheStorage

    mock_ad = Advertisement(
        id=1,
        user_id=1,
        name="Test",
        description="Desc",
        category=1,
        images_qty=5,
    )

    async def mock_get_by_id(self, ad_id):
        return mock_ad if ad_id == 1 else None

    async def mock_get_task_ids(self, item_id):
        return [10, 11]

    async def mock_delete_by_item_id(self, item_id):
        pass

    async def mock_close_ad(self, ad_id):
        return True

    monkeypatch.setattr(AdvertisementRepository, "get_by_id", mock_get_by_id)
    monkeypatch.setattr(ModerationResultRepository, "get_task_ids_by_item_id", mock_get_task_ids)
    monkeypatch.setattr(ModerationResultRepository, "delete_by_item_id", mock_delete_by_item_id)
    monkeypatch.setattr(AdvertisementRepository, "close", mock_close_ad)
    monkeypatch.setattr(PredictionCacheStorage, "delete_prediction_by_ad", AsyncMock())
    monkeypatch.setattr(PredictionCacheStorage, "delete_moderation_results_by_task_ids", AsyncMock())

    response = client.post("/close", json={"item_id": 1})
    assert response.status_code == 200
    assert "closed" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_worker_sends_to_dlq_when_ad_not_found(monkeypatch):
    from app.workers.moderation_worker import process_message
    from app.clients.kafka import KafkaProducerClient

    ad_repo = AdvertisementRepository()
    mod_repo = ModerationResultRepository()
    kafka = KafkaProducerClient()

    async def mock_get_with_user(self, ad_id):
        return None

    monkeypatch.setattr(AdvertisementRepository, "get_with_user", mock_get_with_user)

    set_failed_calls = []
    async def mock_set_failed(self, task_id, error_message):
        set_failed_calls.append((task_id, error_message))

    send_to_dlq_calls = []
    async def mock_send_to_dlq(self, original_message, error, retry_count=1):
        send_to_dlq_calls.append((original_message, error, retry_count))

    monkeypatch.setattr(ModerationResultRepository, "set_failed", mock_set_failed)
    monkeypatch.setattr(KafkaProducerClient, "send_to_dlq", mock_send_to_dlq)

    message = {"item_id": 999, "task_id": 1, "timestamp": "2025-02-04T12:00:00Z"}
    await process_message(message, ad_repo, mod_repo, kafka)

    assert len(set_failed_calls) == 1
    assert set_failed_calls[0][0] == 1
    assert "not found" in set_failed_calls[0][1].lower()
    assert len(send_to_dlq_calls) == 1
    assert send_to_dlq_calls[0][0] == message
    assert send_to_dlq_calls[0][2] == 1

import pytest
from fastapi.testclient import TestClient
from main import app
from services.ml_model import ModelClient
from repositories.advertisements import AdvertisementRepository
from repositories.users import UserRepository
from models.domain import UserCreate, AdvertisementCreate, User, Advertisement, AdvertisementWithUser


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


@pytest.mark.parametrize("name,description,expected_status", [
    ("", "Valid description", 200),
    ("Valid name", "", 200),
    ("Name", "A" * 5000, 200),
    ("A" * 1000, "Description", 200),
])
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

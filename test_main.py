from _pytest import monkeypatch
import pytest
from fastapi.testclient import TestClient
from main import app
from services.ml_model import _model
import services.ml_model as ml_model_module

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_lifespan():
    with TestClient(app) as c:
        yield c

def test_predict_verified_seller():
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
    assert isinstance(data["is_violation"], bool)
    assert isinstance(data["probability"], float)
    assert data["is_violation"] is False 

def test_predict_violation_case():
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


def test_validation_error():
    payload = {
        "seller_id": 3,
        "item_id": 102,
        "name": "Test Item 3",
        "description": "Description 3",
        "category": 3,
        "images_qty": 0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422

def test_model_not_loaded_503(monkeypatch):
    monkeypatch.setattr(ml_model_module,"_model", None)

    payload = {
        "seller_id": 4,
        "is_verified_seller": True,
        "item_id": 103,
        "name": "Test Item 4",
        "description": "Description 4",
        "category": 4,
        "images_qty": 0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 503
    assert response.json()["detail"] == "Model is not loaded"

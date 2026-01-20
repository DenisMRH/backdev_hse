from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_predict_verified_seller():
    payload = {
        "seller_id": 1,
        "is_verified_seller": True,
        "item_id": 100,
        "name": "Test Item",
        "description": "Description",
        "category": 1,
        "images_qty": 0 
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json() is True

def test_predict_unverified_seller_with_images():
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
    assert response.json() is True

def test_predict_unverified_seller_no_images():
    payload = {
        "seller_id": 3,
        "is_verified_seller": False,
        "item_id": 102,
        "name": "Test Item 3",
        "description": "Description 3",
        "category": 3,
        "images_qty": 0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json() is False

def test_predict_validation_missing_field():
    payload = {
        "seller_id": 4,
        "item_id": 103,
        "name": "Test Item 4",
        "description": "Description 4",
        "category": 4,
        "images_qty": 1
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422

def test_predict_validation_wrong_type():
    payload = {
        "seller_id": 5,
        "is_verified_seller": False, 
        "item_id": 104,
        "name": "Test Item 5",
        "description": "Description 5",
        "category": 5,
        "images_qty": "two"
    }
    
    response = client.post("/predict", json=payload)
    assert response.status_code == 422

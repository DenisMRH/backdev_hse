from fastapi import responses
from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)


@pytest.mark.parametrize(
    "test_case_name, payload, expected_status, expected_response",
    [
        (
            "verified_seller",
            {
                "seller_id": 1,
                "is_verified_seller": True,
                "item_id": 100,
                "name": "Test Item",
                "description": "Description",
                "category": 1,
                "images_qty": 0 
            },
            200,
            True
        )   ,

        (
            "unverified_seller_with_images",
            {
                "seller_id": 1,
                "is_verified_seller": False,
                "item_id": 100,
                "name": "Test Item",
                "description": "Description",
                "category": 1,
                "images_qty": 1
            },
            200,
            True
        )   ,

        (
            "unverified_seller_no_images",
            {
                "seller_id": 1,
                "is_verified_seller": False,
                "item_id": 100,
                "name": "Test Item",
                "description": "Description",
                "category": 1,
                "images_qty": 0 
            },
            200,
            False
        )   ,

        (
            "validation_missing_field",
            {
                "seller_id": 1,
                "item_id": 100,
                "name": "Test Item",
                "description": "Description",
                "category": 1,
                "images_qty": 0 
            },
            422,
            False
        )   ,

        (
            "validation_wrong_type",
            {
                "seller_id": 1,
                "is_verified_seller": True,
                "item_id": 100,
                "name": "Test Item",
                "description": "Description",
                "category": 1,
                "images_qty": "two"
            },
            422,
            False
        )   
    ]
)

def test_predict(test_case_name, payload, expected_status, expected_response):
    response = client.post("/predict", json=payload)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json() == expected_response


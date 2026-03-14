"""
Tests for Product endpoints
"""

import pytest
import unittest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.schemas.product import ProductCreate, ProductResponse

client = TestClient(app)


@pytest.fixture
def product_create_payload():
    return {
        "name": "Test T-Shirt",
        "slug": "test-t-shirt",
        "description": "A high-quality test t-shirt.",
        "category_id": 1,
        "base_price": 19.99,
        "variants": [
            {
                "name": "Small",
                "sku": "TS-SM",
                "price_adjustment": 0,
                "attributes": {"size": "S", "color": "Black"},
                "inventory_quantity": 100
            }
        ]
    }


@pytest.fixture
def product_response_payload():
    return {
        "id": 1,
        "name": "Test T-Shirt",
        "slug": "test-t-shirt",
        "description": "A high-quality test t-shirt.",
        "category_id": 1,
        "base_price": 19.99,
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z",
        "category": {
            "id": 1,
            "name": "T-Shirts",
            "slug": "t-shirts",
            "created_at": "2025-01-01T12:00:00Z",
            "updated_at": "2025-01-01T12:00:00Z"
        },
        "variants": [
            {
                "id": 1,
                "product_id": 1,
                "name": "Small",
                "sku": "TS-SM",
                "price_adjustment": 0,
                "attributes": {"size": "S", "color": "Black"},
                "inventory_quantity": 100,
                "created_at": "2025-01-01T12:00:00Z",
                "updated_at": "2025-01-01T12:00:00Z"
            }
        ]
    }


@patch("app.services.product.product_service.create", new_callable=AsyncMock)
def test_create_product(mock_create, product_create_payload, product_response_payload):
    """Test creating a product"""
    mock_create.return_value = ProductResponse(**product_response_payload)

    response = client.post("/api/v1/products/", json=product_create_payload)

    assert response.status_code == 201
    # The response from the test client will be a dict, not a Pydantic model
    # We can't directly compare it to the Pydantic model, so we check for key fields
    assert response.json()["name"] == product_create_payload["name"]
    assert response.json()["slug"] == product_create_payload["slug"]
    mock_create.assert_called_once()


@patch("app.services.product.product_service.get_all", new_callable=AsyncMock)
def test_get_products(mock_get_all, product_response_payload):
    """Test getting all products"""
    mock_get_all.return_value = [ProductResponse(**product_response_payload)]

    response = client.get("/api/v1/products/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == product_response_payload["name"]
    mock_get_all.assert_called_once()


@patch("app.services.product.product_service.get", new_callable=AsyncMock)
def test_get_product(mock_get, product_response_payload):
    """Test getting a single product by ID"""
    mock_get.return_value = ProductResponse(**product_response_payload)

    response = client.get("/api/v1/products/1")

    assert response.status_code == 200
    assert response.json()["name"] == product_response_payload["name"]
    mock_get.assert_called_once_with(db=unittest.mock.ANY, id=1)


@patch("app.services.product.product_service.get", new_callable=AsyncMock)
def test_get_product_not_found(mock_get):
    """Test getting a product that does not exist"""
    mock_get.return_value = None

    response = client.get("/api/v1/products/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Product not found"}
    mock_get.assert_called_once_with(db=unittest.mock.ANY, id=999)


@patch("app.services.product.product_service.get", new_callable=AsyncMock)
@patch("app.services.product.product_service.update", new_callable=AsyncMock)
def test_update_product(mock_update, mock_get, product_response_payload):
    """Test updating a product"""
    update_payload = {"name": "Updated Test T-Shirt"}
    updated_product_payload = product_response_payload.copy()
    updated_product_payload["name"] = "Updated Test T-Shirt"

    mock_get.return_value = ProductResponse(**product_response_payload)
    mock_update.return_value = ProductResponse(**updated_product_payload)

    response = client.put("/api/v1/products/1", json=update_payload)

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Test T-Shirt"
    mock_get.assert_called_once_with(db=unittest.mock.ANY, id=1)
    mock_update.assert_called_once()


@patch("app.services.product.product_service.get", new_callable=AsyncMock)
@patch("app.services.product.product_service.delete", new_callable=AsyncMock)
def test_delete_product(mock_delete, mock_get, product_response_payload):
    """Test deleting a product"""
    mock_get.return_value = ProductResponse(**product_response_payload)
    mock_delete.return_value = None

    response = client.delete("/api/v1/products/1")

    assert response.status_code == 204
    mock_get.assert_called_once_with(db=unittest.mock.ANY, id=1)
    mock_delete.assert_called_once()
import pytest
from fastapi.testclient import TestClient
from app.schemas.product import ProductCreate

def test_list_products_unauthenticated(client: TestClient):
    """Test listing products without authentication (public endpoint)"""
    response = client.get("/api/v1/products/")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_create_product_as_seller(seller_client):
    """Test creating product as seller"""
    with seller_client as client:
        product_data = {
            "title": "Test Product",
            "description": "Test Description",
            "price": 29.99,
            "stock_quantity": 100
        }
        
        response = client.post("/api/v1/products/", json=product_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == product_data["title"]
        assert data["price"] == product_data["price"]

def test_create_product_as_customer(customer_client):
    """Test creating product as customer (should fail)"""
    with customer_client() as client:
        product_data = {
            "title": "Test Product",
            "description": "Test Description", 
            "price": 29.99,
            "stock_quantity": 100
        }
        
        response = client.post("/api/v1/products/", json=product_data)
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

def test_create_product_unauthenticated(client: TestClient):
    """Test creating product without authentication"""
    product_data = {
        "title": "Test Product",
        "description": "Test Description",
        "price": 29.99,
        "stock_quantity": 100
    }
    
    response = client.post("/api/v1/products/", json=product_data)
    
    assert response.status_code == 401

def test_delete_product_as_admin(admin_client):
    """Test admin deleting a product"""
    with admin_client as client:
        # Create a product first
        product_data = {
            "title": "Product to Delete",
            "description": "Will be deleted",
            "price": 15.99,
            "stock_quantity": 25
        }
        
        create_response = client.post("/api/v1/products/", json=product_data)
        assert create_response.status_code == 201
        product_id = create_response.json()["id"]
        
        # Delete as admin
        response = client.delete(f"/api/v1/products/{product_id}")
        
        assert response.status_code == 204

def test_delete_product_as_seller(seller_client):
    """Test seller trying to delete product (should fail)"""
    with seller_client as client:
        # Create a product
        product_data = {
            "title": "Product to Delete",
            "description": "Will be deleted",
            "price": 15.99,
            "stock_quantity": 25
        }
        
        create_response = client.post("/api/v1/products/", json=product_data)
        assert create_response.status_code == 201
        product_id = create_response.json()["id"]
        
        # Try to delete as seller
        response = client.delete(f"/api/v1/products/{product_id}")
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

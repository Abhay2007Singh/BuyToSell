import pytest
from fastapi.testclient import TestClient

def test_create_order_as_customer(customer_client):
    """Test creating order as customer"""
    with customer_client as client:
        # First create a product to order
        product_data = {
            "title": "Order Test Product",
            "description": "Product for testing orders",
            "price": 49.99,
            "stock_quantity": 100
        }
        
        product_response = client.post("/api/v1/products/", json=product_data)
        product_id = product_response.json()["id"]
        
        # Create order
        order_data = {
            "user_id": 1,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                    "price": 49.99
                }
            ]
        }
        
        response = client.post("/api/v1/orders/", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == order_data["user_id"]
        assert "id" in data

def test_create_order_as_seller(seller_client):
    """Test creating order as seller (should fail)"""
    with seller_client() as client:
        order_data = {
            "user_id": 1,
            "items": [
                {
                    "product_id": 1,
                    "quantity": 1,
                    "price": 29.99
                }
            ]
        }
        
        response = client.post("/api/v1/orders/", json=order_data)
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

def test_get_own_orders(customer_client):
    """Test customer getting their own orders"""
    with customer_client as client:
        response = client.get("/api/v1/orders/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

def test_update_order_status_as_admin(admin_client):
    """Test admin updating order status"""
    with admin_client as client:
        status_data = {"status": "shipped"}
        
        # Try updating an order (even non-existent one for test)
        response = client.put("/api/v1/orders/1/status", json=status_data)
        
        # Should either succeed (if order exists) or fail with 404 (if not)
        assert response.status_code in [200, 404]

def test_update_order_status_as_customer(customer_client):
    """Test customer trying to update order status (should fail)"""
    with customer_client as client:
        status_data = {"status": "shipped"}
        
        response = client.put("/api/v1/orders/1/status", json=status_data)
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

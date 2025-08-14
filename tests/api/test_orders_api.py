"""Tests for Order API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel

from orders_inventory.api.main import app
from orders_inventory.models.base import get_db_session
from orders_inventory.models import OrderStatus


@pytest.fixture(scope="function")
def test_client():
    """Create test client with in-memory database."""
    # Create test database
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    
    def get_test_db():
        with Session(engine) as session:
            yield session
    
    # Override dependency
    app.dependency_overrides[get_db_session] = get_test_db
    
    with TestClient(app) as client:
        yield client
    
    # Cleanup
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def sample_product(test_client):
    """Create a sample product for testing."""
    response = test_client.post("/products/", json={
        "sku": "ORDER_PROD001",
        "name": "Order Test Product",
        "price": 25.99,
        "stock": 100
    })
    return response.json()


class TestOrderEndpoints:
    """Test Order API endpoints."""
    
    def test_create_order_success(self, test_client, sample_product):
        """Test successful order creation."""
        order_data = {
            "product_id": sample_product["id"],
            "quantity": 10
        }
        
        response = test_client.post("/orders/", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == sample_product["id"]
        assert data["quantity"] == 10
        assert data["status"] == "PENDING"
        assert "id" in data
        assert "created_at" in data
        
        # Verify stock was reduced
        product_response = test_client.get(f"/products/{sample_product['id']}")
        updated_product = product_response.json()
        assert updated_product["stock"] == 90  # 100 - 10
    
    def test_create_order_product_not_found(self, test_client):
        """Test creating order for non-existent product returns 404."""
        order_data = {
            "product_id": 99999,
            "quantity": 10
        }
        
        response = test_client.post("/orders/", json=order_data)
        
        assert response.status_code == 404
        assert "Product with ID 99999 not found" in response.json()["detail"]
    
    def test_create_order_insufficient_stock(self, test_client, sample_product):
        """Test creating order with insufficient stock returns 409."""
        order_data = {
            "product_id": sample_product["id"],
            "quantity": 150  # More than available stock (100)
        }
        
        response = test_client.post("/orders/", json=order_data)
        
        assert response.status_code == 409
        assert "Insufficient stock" in response.json()["detail"]
        
        # Verify stock was not modified
        product_response = test_client.get(f"/products/{sample_product['id']}")
        updated_product = product_response.json()
        assert updated_product["stock"] == 100  # Unchanged
    
    def test_create_order_validation_error(self, test_client, sample_product):
        """Test order creation with validation errors."""
        # Invalid quantity (zero)
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 0
        })
        assert response.status_code == 422
        
        # Invalid quantity (negative)
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": -5
        })
        assert response.status_code == 422
        
        # Missing required field
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"]
            # missing quantity
        })
        assert response.status_code == 422
    
    def test_list_orders_empty(self, test_client):
        """Test listing orders when none exist."""
        response = test_client.get("/orders/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["orders"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20
    
    def test_list_orders_with_filters(self, test_client, sample_product):
        """Test listing orders with filters."""
        # Create orders with different statuses
        order1_response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 5
        })
        order1_id = order1_response.json()["id"]
        
        order2_response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 3
        })
        order2_id = order2_response.json()["id"]
        
        # Mark one as paid
        test_client.post(f"/orders/{order2_id}/pay")
        
        # Test status filter - pending orders
        response = test_client.get("/orders/?status=PENDING")
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 1
        assert data["orders"][0]["id"] == order1_id
        
        # Test status filter - paid orders
        response = test_client.get("/orders/?status=PAID")
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 1
        assert data["orders"][0]["id"] == order2_id
        
        # Test product filter
        response = test_client.get(f"/orders/?product_id={sample_product['id']}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 2
    
    def test_get_order_success(self, test_client, sample_product):
        """Test getting order details."""
        # Create order
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 8
        })
        order_id = response.json()["id"]
        
        # Get order details
        response = test_client.get(f"/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["product_id"] == sample_product["id"]
        assert data["quantity"] == 8
        assert data["status"] == "PENDING"
        
        # Should include product details
        assert data["product"] is not None
        assert data["product"]["sku"] == sample_product["sku"]
        assert data["product"]["name"] == sample_product["name"]
        
        # Should include total value
        assert data["total_value"] == 25.99 * 8
    
    def test_get_order_not_found(self, test_client):
        """Test getting non-existent order returns 404."""
        response = test_client.get("/orders/99999")
        
        assert response.status_code == 404
        assert "Order with ID 99999 not found" in response.json()["detail"]
    
    def test_update_order_quantity_success(self, test_client, sample_product):
        """Test successful order quantity update."""
        # Create order
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 10
        })
        order_id = response.json()["id"]
        
        # Update quantity
        response = test_client.put(f"/orders/{order_id}", json={"quantity": 15})
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 15
        
        # Verify stock adjustment
        product_response = test_client.get(f"/products/{sample_product['id']}")
        updated_product = product_response.json()
        assert updated_product["stock"] == 85  # 100 - 15
    
    def test_update_order_quantity_insufficient_stock(self, test_client, sample_product):
        """Test order quantity update with insufficient stock."""
        # Create order
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 10
        })
        order_id = response.json()["id"]
        
        # Try to update to more than available stock
        response = test_client.put(f"/orders/{order_id}", json={"quantity": 150})
        
        assert response.status_code == 409
        assert "Insufficient stock" in response.json()["detail"]
    
    def test_update_order_quantity_non_pending_order(self, test_client, sample_product):
        """Test quantity update only allowed for pending orders."""
        # Create and pay for order
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 10
        })
        order_id = response.json()["id"]
        test_client.post(f"/orders/{order_id}/pay")
        
        # Try to update quantity
        response = test_client.put(f"/orders/{order_id}", json={"quantity": 15})
        
        assert response.status_code == 422
        assert "Cannot change quantity for PAID orders" in response.json()["detail"]
    
    def test_order_status_transitions(self, test_client, sample_product):
        """Test order status transitions."""
        # Create order
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 10
        })
        order_id = response.json()["id"]
        
        # PENDING → PAID
        response = test_client.post(f"/orders/{order_id}/pay")
        assert response.status_code == 200
        assert response.json()["status"] == "PAID"
        
        # PAID → SHIPPED
        response = test_client.post(f"/orders/{order_id}/ship")
        assert response.status_code == 200
        assert response.json()["status"] == "SHIPPED"
        
        # Try invalid transition (SHIPPED → anything)
        response = test_client.post(f"/orders/{order_id}/cancel")
        assert response.status_code == 422
        assert "Cannot cancel a shipped order" in response.json()["detail"]
    
    def test_cancel_order_restores_stock(self, test_client, sample_product):
        """Test order cancellation restores stock."""
        # Create and pay for order
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 20
        })
        order_id = response.json()["id"]
        test_client.post(f"/orders/{order_id}/pay")
        
        # Verify stock was reduced
        product_response = test_client.get(f"/products/{sample_product['id']}")
        assert product_response.json()["stock"] == 80  # 100 - 20
        
        # Cancel order
        response = test_client.post(f"/orders/{order_id}/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "CANCELED"
        
        # Verify stock was restored
        product_response = test_client.get(f"/products/{sample_product['id']}")
        assert product_response.json()["stock"] == 100  # Back to original
    
    def test_delete_order_cancel_semantics(self, test_client, sample_product):
        """Test order deletion uses cancel semantics by default."""
        # Create order
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 15
        })
        order_id = response.json()["id"]
        
        # Delete order (should cancel)
        response = test_client.delete(f"/orders/{order_id}")
        
        assert response.status_code == 200
        assert "canceled successfully" in response.json()["message"]
        
        # Order should still exist but be canceled
        order_response = test_client.get(f"/orders/{order_id}")
        assert order_response.status_code == 200
        assert order_response.json()["status"] == "CANCELED"
        
        # Stock should be restored
        product_response = test_client.get(f"/products/{sample_product['id']}")
        assert product_response.json()["stock"] == 100
    
    def test_delete_order_force_delete(self, test_client, sample_product):
        """Test forced order deletion removes record."""
        # Create order
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 15
        })
        order_id = response.json()["id"]
        
        # Force delete order
        response = test_client.delete(f"/orders/{order_id}?force=true")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Order should no longer exist
        order_response = test_client.get(f"/orders/{order_id}")
        assert order_response.status_code == 404
    
    def test_delete_order_not_found(self, test_client):
        """Test deleting non-existent order returns 404."""
        response = test_client.delete("/orders/99999")
        
        assert response.status_code == 404
        assert "Order with ID 99999 not found" in response.json()["detail"]
    
    def test_get_recent_orders(self, test_client, sample_product):
        """Test getting recent orders."""
        # Create multiple orders
        order_ids = []
        for i in range(5):
            response = test_client.post("/orders/", json={
                "product_id": sample_product["id"],
                "quantity": i + 1
            })
            order_ids.append(response.json()["id"])
        
        # Get recent orders
        response = test_client.get("/orders/recent?limit=3")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Should be in descending order (most recent first)
        assert data[0]["id"] == order_ids[-1]  # Last created
        assert data[1]["id"] == order_ids[-2]
        assert data[2]["id"] == order_ids[-3]
    
    def test_order_workflow_validation(self, test_client, sample_product):
        """Test complete order workflow validation."""
        # Create order
        response = test_client.post("/orders/", json={
            "product_id": sample_product["id"],
            "quantity": 10
        })
        order_id = response.json()["id"]
        
        # Try to ship pending order (should fail)
        response = test_client.post(f"/orders/{order_id}/ship")
        assert response.status_code == 422
        assert "Cannot ship order" in response.json()["detail"]
        
        # Pay for order
        response = test_client.post(f"/orders/{order_id}/pay")
        assert response.status_code == 200
        
        # Now shipping should work
        response = test_client.post(f"/orders/{order_id}/ship")
        assert response.status_code == 200
        
        # Try to pay shipped order (should fail)
        response = test_client.post(f"/orders/{order_id}/pay")
        assert response.status_code == 422

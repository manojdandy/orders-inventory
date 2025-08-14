"""Tests for Product API endpoints."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel

from orders_inventory.api.main import app
from orders_inventory.models.base import get_db_session


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


class TestProductEndpoints:
    """Test Product API endpoints."""
    
    def test_create_product_success(self, test_client):
        """Test successful product creation."""
        product_data = {
            "sku": "TEST001",
            "name": "Test Product",
            "price": 19.99,
            "stock": 100
        }
        
        response = test_client.post("/products/", json=product_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["sku"] == "TEST001"
        assert data["name"] == "Test Product"
        assert data["price"] == 19.99
        assert data["stock"] == 100
        assert "id" in data
    
    def test_create_product_duplicate_sku(self, test_client):
        """Test creating product with duplicate SKU returns 409."""
        product_data = {
            "sku": "DUP001",
            "name": "First Product",
            "price": 19.99,
            "stock": 100
        }
        
        # Create first product
        response = test_client.post("/products/", json=product_data)
        assert response.status_code == 201
        
        # Try to create duplicate
        product_data["name"] = "Duplicate Product"
        response = test_client.post("/products/", json=product_data)
        
        assert response.status_code == 409
        assert "SKU 'DUP001' already exists" in response.json()["detail"]
    
    def test_create_product_validation_error(self, test_client):
        """Test product creation with validation errors."""
        # Invalid price (negative)
        response = test_client.post("/products/", json={
            "sku": "TEST001",
            "name": "Test Product",
            "price": -10.00,
            "stock": 100
        })
        assert response.status_code == 422
        
        # Missing required field
        response = test_client.post("/products/", json={
            "sku": "TEST001",
            "name": "Test Product",
            "price": 19.99
            # missing stock
        })
        assert response.status_code == 422
    
    def test_list_products_empty(self, test_client):
        """Test listing products when none exist."""
        response = test_client.get("/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["products"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20
    
    def test_list_products_with_pagination(self, test_client):
        """Test listing products with pagination."""
        # Create multiple products
        for i in range(25):
            test_client.post("/products/", json={
                "sku": f"PROD{i:03d}",
                "name": f"Product {i}",
                "price": 10.00 + i,
                "stock": 50 + i
            })
        
        # Test first page
        response = test_client.get("/products/?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["total_pages"] == 3
        
        # Test second page
        response = test_client.get("/products/?page=2&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 10
        assert data["page"] == 2
    
    def test_list_products_with_filters(self, test_client):
        """Test listing products with filters."""
        # Create test products
        products = [
            {"sku": "HIGH001", "name": "High Stock", "price": 10.00, "stock": 100},
            {"sku": "LOW001", "name": "Low Stock", "price": 15.00, "stock": 5},
            {"sku": "OUT001", "name": "Out of Stock", "price": 20.00, "stock": 0},
        ]
        
        for product in products:
            test_client.post("/products/", json=product)
        
        # Test in_stock_only filter
        response = test_client.get("/products/?in_stock_only=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 2  # HIGH001 and LOW001
        
        # Test low_stock_threshold filter
        response = test_client.get("/products/?low_stock_threshold=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 2  # LOW001 and OUT001
        
        # Test price range filter
        response = test_client.get("/products/?min_price=12&max_price=18")
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 1  # LOW001
        
        # Test search filter
        response = test_client.get("/products/?search=High")
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 1  # HIGH001
    
    def test_get_product_success(self, test_client):
        """Test getting product by ID."""
        # Create product
        response = test_client.post("/products/", json={
            "sku": "GET001",
            "name": "Get Product",
            "price": 25.99,
            "stock": 50
        })
        product_id = response.json()["id"]
        
        # Get product
        response = test_client.get(f"/products/{product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == "GET001"
        assert data["name"] == "Get Product"
        assert data["price"] == 25.99
        assert data["stock"] == 50
    
    def test_get_product_not_found(self, test_client):
        """Test getting non-existent product returns 404."""
        response = test_client.get("/products/99999")
        
        assert response.status_code == 404
        assert "Product with ID 99999 not found" in response.json()["detail"]
    
    def test_update_product_success(self, test_client):
        """Test successful product update."""
        # Create product
        response = test_client.post("/products/", json={
            "sku": "UPD001",
            "name": "Original Product",
            "price": 19.99,
            "stock": 100
        })
        product_id = response.json()["id"]
        
        # Update product (partial)
        update_data = {
            "name": "Updated Product",
            "price": 29.99
        }
        response = test_client.put(f"/products/{product_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product"
        assert data["price"] == 29.99
        assert data["sku"] == "UPD001"  # Unchanged
        assert data["stock"] == 100  # Unchanged
    
    def test_update_product_not_found(self, test_client):
        """Test updating non-existent product returns 404."""
        response = test_client.put("/products/99999", json={"name": "New Name"})
        
        assert response.status_code == 404
        assert "Product with ID 99999 not found" in response.json()["detail"]
    
    def test_update_product_validation_error(self, test_client):
        """Test product update with validation errors."""
        # Create product
        response = test_client.post("/products/", json={
            "sku": "VAL001",
            "name": "Validation Product",
            "price": 19.99,
            "stock": 100
        })
        product_id = response.json()["id"]
        
        # Invalid price update
        response = test_client.put(f"/products/{product_id}", json={"price": -10.00})
        assert response.status_code == 422
    
    def test_delete_product_success(self, test_client):
        """Test successful product deletion."""
        # Create product
        response = test_client.post("/products/", json={
            "sku": "DEL001",
            "name": "Delete Product",
            "price": 19.99,
            "stock": 100
        })
        product_id = response.json()["id"]
        
        # Delete product
        response = test_client.delete(f"/products/{product_id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        response = test_client.get(f"/products/{product_id}")
        assert response.status_code == 404
    
    def test_delete_product_not_found(self, test_client):
        """Test deleting non-existent product returns 404."""
        response = test_client.delete("/products/99999")
        
        assert response.status_code == 404
        assert "Product with ID 99999 not found" in response.json()["detail"]
    
    def test_get_product_by_sku(self, test_client):
        """Test getting product by SKU."""
        # Create product
        test_client.post("/products/", json={
            "sku": "SKU001",
            "name": "SKU Product",
            "price": 19.99,
            "stock": 100
        })
        
        # Get by SKU
        response = test_client.get("/products/sku/SKU001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == "SKU001"
        assert data["name"] == "SKU Product"
    
    def test_adjust_stock(self, test_client):
        """Test stock adjustment endpoint."""
        # Create product
        response = test_client.post("/products/", json={
            "sku": "STOCK001",
            "name": "Stock Product",
            "price": 19.99,
            "stock": 100
        })
        product_id = response.json()["id"]
        
        # Adjust stock
        response = test_client.post(
            f"/products/{product_id}/stock/adjust",
            json={"adjustment": -20, "reason": "Sale"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["stock"] == 80  # 100 - 20

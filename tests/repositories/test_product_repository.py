"""Tests for ProductRepository."""

import pytest
from decimal import Decimal

from orders_inventory.models import Product


class TestProductRepository:
    """Test ProductRepository operations."""
    
    def test_create_product(self, product_repository, sample_product):
        """Test creating a product in database."""
        created = product_repository.create(sample_product)
        
        assert created.id is not None
        assert created.sku == "TEST001"
        assert created.name == "Test Product"
        assert created.price == Decimal("19.99")
        assert created.stock == 100
    
    def test_get_by_id(self, product_repository, created_product):
        """Test getting product by ID."""
        retrieved = product_repository.get_by_id(created_product.id)
        assert retrieved is not None
        assert retrieved.sku == created_product.sku
        assert retrieved.name == created_product.name
    
    def test_get_by_id_not_found(self, product_repository):
        """Test getting product by non-existent ID returns None."""
        retrieved = product_repository.get_by_id(99999)
        assert retrieved is None
    
    def test_get_by_sku(self, product_repository, created_product):
        """Test getting product by SKU."""
        retrieved = product_repository.get_by_sku(created_product.sku)
        assert retrieved is not None
        assert retrieved.id == created_product.id
        assert retrieved.sku == created_product.sku
    
    def test_get_by_sku_case_insensitive(self, product_repository, created_product):
        """Test getting product by SKU is case insensitive."""
        retrieved = product_repository.get_by_sku(created_product.sku.lower())
        assert retrieved is not None
        assert retrieved.id == created_product.id
    
    def test_get_by_sku_not_found(self, product_repository):
        """Test getting product by non-existent SKU returns None."""
        retrieved = product_repository.get_by_sku("NONEXISTENT")
        assert retrieved is None
    
    def test_get_all_empty(self, product_repository):
        """Test getting all products when repository is empty."""
        products = product_repository.get_all()
        assert products == []
    
    def test_get_all_with_products(self, product_repository, created_products):
        """Test getting all products."""
        products = product_repository.get_all()
        assert len(products) == 3
        skus = [p.sku for p in products]
        assert "PROD001" in skus
        assert "PROD002" in skus
        assert "PROD003" in skus
    
    def test_update_product(self, product_repository, created_product):
        """Test updating a product."""
        created_product.name = "Updated Product Name"
        created_product.price = Decimal("99.99")
        
        updated = product_repository.update(created_product)
        
        assert updated.name == "Updated Product Name"
        assert updated.price == Decimal("99.99")
        assert updated.id == created_product.id
    
    def test_delete_product(self, product_repository, created_product):
        """Test deleting a product."""
        product_id = created_product.id
        
        result = product_repository.delete(product_id)
        assert result is True
        
        # Verify product is deleted
        retrieved = product_repository.get_by_id(product_id)
        assert retrieved is None
    
    def test_delete_nonexistent_product(self, product_repository):
        """Test deleting non-existent product returns False."""
        result = product_repository.delete(99999)
        assert result is False
    
    def test_search_by_name(self, product_repository, created_products):
        """Test searching products by name pattern."""
        # Search for "Product" - should match all 3
        results = product_repository.search_by_name("Product")
        assert len(results) == 3
        
        # Search for "One" - should match only "Product One"
        results = product_repository.search_by_name("One")
        assert len(results) == 1
        assert results[0].name == "Product One"
        
        # Search for non-existent pattern
        results = product_repository.search_by_name("Nonexistent")
        assert len(results) == 0
    
    def test_get_low_stock(self, product_repository, created_products):
        """Test getting products with low stock."""
        # Default threshold (10) - should return PROD003 (stock=0)
        low_stock = product_repository.get_low_stock()
        assert len(low_stock) == 1
        assert low_stock[0].sku == "PROD003"
        
        # Higher threshold (40) - should return PROD002 (stock=30) and PROD003 (stock=0)
        low_stock = product_repository.get_low_stock(40)
        assert len(low_stock) == 2
        skus = [p.sku for p in low_stock]
        assert "PROD002" in skus
        assert "PROD003" in skus
        
        # Very high threshold (100) - should return all products
        low_stock = product_repository.get_low_stock(100)
        assert len(low_stock) == 3
    
    def test_get_by_price_range(self, product_repository, created_products):
        """Test getting products within price range."""
        # Range 5.00 to 15.00 - should return PROD001 and PROD003
        results = product_repository.get_by_price_range(5.00, 15.00)
        assert len(results) == 2
        skus = [p.sku for p in results]
        assert "PROD001" in skus
        assert "PROD003" in skus
        
        # Range 20.00 to 30.00 - should return PROD002
        results = product_repository.get_by_price_range(20.00, 30.00)
        assert len(results) == 1
        assert results[0].sku == "PROD002"
        
        # Range outside all prices
        results = product_repository.get_by_price_range(100.00, 200.00)
        assert len(results) == 0
    
    def test_get_in_stock(self, product_repository, created_products):
        """Test getting products that are in stock."""
        in_stock = product_repository.get_in_stock()
        assert len(in_stock) == 2  # PROD001 and PROD002 have stock > 0
        skus = [p.sku for p in in_stock]
        assert "PROD001" in skus
        assert "PROD002" in skus
        assert "PROD003" not in skus  # This one has stock = 0
    
    def test_get_out_of_stock(self, product_repository, created_products):
        """Test getting products that are out of stock."""
        out_of_stock = product_repository.get_out_of_stock()
        assert len(out_of_stock) == 1  # Only PROD003 has stock = 0
        assert out_of_stock[0].sku == "PROD003"
    
    def test_count(self, product_repository, created_products):
        """Test counting products."""
        count = product_repository.count()
        assert count == 3

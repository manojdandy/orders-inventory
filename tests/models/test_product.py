"""Tests for Product model."""

import pytest
from decimal import Decimal

from orders_inventory.models import Product


class TestProductModel:
    """Test Product model validation and constraints."""
    
    def test_product_creation_valid(self):
        """Test creating a valid product."""
        product = Product(
            sku="ABC123",
            name="Test Product",
            price=Decimal("29.99"),
            stock=50
        )
        assert product.sku == "ABC123"
        assert product.name == "Test Product"
        assert product.price == Decimal("29.99")
        assert product.stock == 50
    
    def test_sku_validation_uppercase(self):
        """Test SKU is converted to uppercase."""
        product = Product(
            sku="abc123",
            name="Test Product", 
            price=Decimal("29.99"),
            stock=50
        )
        assert product.sku == "ABC123"
    
    def test_sku_validation_empty(self):
        """Test empty SKU raises ValueError."""
        with pytest.raises(ValueError, match="SKU cannot be empty"):
            Product(
                sku="",
                name="Test Product",
                price=Decimal("29.99"),
                stock=50
            )
    
    def test_sku_validation_whitespace_only(self):
        """Test whitespace-only SKU raises ValueError."""
        with pytest.raises(ValueError, match="SKU cannot be empty"):
            Product(
                sku="   ",
                name="Test Product",
                price=Decimal("29.99"),
                stock=50
            )
    
    def test_sku_validation_too_long(self):
        """Test SKU longer than 50 characters raises ValueError."""
        long_sku = "A" * 51
        with pytest.raises(ValueError, match="SKU cannot exceed 50 characters"):
            Product(
                sku=long_sku,
                name="Test Product",
                price=Decimal("29.99"),
                stock=50
            )
    
    def test_sku_validation_strips_whitespace(self):
        """Test SKU strips leading/trailing whitespace."""
        product = Product(
            sku="  TEST001  ",
            name="Test Product",
            price=Decimal("29.99"),
            stock=50
        )
        assert product.sku == "TEST001"
    
    def test_name_validation_empty(self):
        """Test empty name raises ValueError."""
        with pytest.raises(ValueError, match="Product name cannot be empty"):
            Product(
                sku="TEST001",
                name="",
                price=Decimal("29.99"),
                stock=50
            )
    
    def test_name_validation_whitespace_only(self):
        """Test whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="Product name cannot be empty"):
            Product(
                sku="TEST001",
                name="   ",
                price=Decimal("29.99"),
                stock=50
            )
    
    def test_name_validation_too_long(self):
        """Test name longer than 200 characters raises ValueError."""
        long_name = "A" * 201
        with pytest.raises(ValueError, match="Product name cannot exceed 200 characters"):
            Product(
                sku="TEST001",
                name=long_name,
                price=Decimal("29.99"),
                stock=50
            )
    
    def test_name_validation_strips_whitespace(self):
        """Test name strips leading/trailing whitespace."""
        product = Product(
            sku="TEST001",
            name="  Test Product  ",
            price=Decimal("29.99"),
            stock=50
        )
        assert product.name == "Test Product"
    
    def test_price_validation_negative(self):
        """Test negative price raises ValueError."""
        with pytest.raises(ValueError, match="Price must be greater than 0"):
            Product(
                sku="TEST001",
                name="Test Product",
                price=Decimal("-10.00"),
                stock=50
            )
    
    def test_price_validation_zero(self):
        """Test zero price raises ValueError."""
        with pytest.raises(ValueError, match="Price must be greater than 0"):
            Product(
                sku="TEST001",
                name="Test Product",
                price=Decimal("0.00"),
                stock=50
            )
    
    def test_price_validation_positive(self):
        """Test positive price is valid."""
        product = Product(
            sku="TEST001",
            name="Test Product",
            price=Decimal("0.01"),
            stock=50
        )
        assert product.price == Decimal("0.01")
    
    def test_stock_validation_negative(self):
        """Test negative stock raises ValueError."""
        with pytest.raises(ValueError, match="Stock cannot be negative"):
            Product(
                sku="TEST001",
                name="Test Product",
                price=Decimal("29.99"),
                stock=-1
            )
    
    def test_stock_validation_zero_allowed(self):
        """Test zero stock is allowed."""
        product = Product(
            sku="TEST001",
            name="Test Product",
            price=Decimal("29.99"),
            stock=0
        )
        assert product.stock == 0
    
    def test_stock_validation_positive(self):
        """Test positive stock is valid."""
        product = Product(
            sku="TEST001",
            name="Test Product",
            price=Decimal("29.99"),
            stock=100
        )
        assert product.stock == 100

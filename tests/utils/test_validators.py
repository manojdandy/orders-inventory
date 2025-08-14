"""Tests for validation utilities."""

import pytest
from decimal import Decimal

from orders_inventory.utils.validators import (
    validate_sku,
    validate_price,
    validate_stock,
    validate_quantity,
    validate_product_name,
    validate_email,
    ValidationError
)


class TestValidateSku:
    """Test SKU validation."""
    
    def test_valid_sku(self):
        """Test valid SKU validation."""
        assert validate_sku("ABC123") == "ABC123"
        assert validate_sku("PROD-001") == "PROD-001"
        assert validate_sku("test_sku") == "TEST_SKU"
        assert validate_sku("a1b2c3") == "A1B2C3"
    
    def test_sku_converts_to_uppercase(self):
        """Test SKU is converted to uppercase."""
        assert validate_sku("abc123") == "ABC123"
        assert validate_sku("Test-SKU") == "TEST-SKU"
        assert validate_sku("mixed_Case_123") == "MIXED_CASE_123"
    
    def test_sku_strips_whitespace(self):
        """Test SKU strips whitespace."""
        assert validate_sku("  ABC123  ") == "ABC123"
        assert validate_sku("\tTEST\n") == "TEST"
    
    def test_sku_empty_raises_error(self):
        """Test empty SKU raises ValidationError."""
        with pytest.raises(ValidationError, match="SKU must be a non-empty string"):
            validate_sku("")
        
        with pytest.raises(ValidationError, match="SKU cannot be empty or whitespace only"):
            validate_sku("   ")
    
    def test_sku_none_raises_error(self):
        """Test None SKU raises ValidationError."""
        with pytest.raises(ValidationError, match="SKU must be a non-empty string"):
            validate_sku(None)
    
    def test_sku_too_long_raises_error(self):
        """Test SKU longer than 50 characters raises ValidationError."""
        long_sku = "A" * 51
        with pytest.raises(ValidationError, match="SKU cannot exceed 50 characters"):
            validate_sku(long_sku)
    
    def test_sku_invalid_characters_raises_error(self):
        """Test SKU with invalid characters raises ValidationError."""
        with pytest.raises(ValidationError, match="SKU can only contain"):
            validate_sku("ABC@123")
        
        with pytest.raises(ValidationError, match="SKU can only contain"):
            validate_sku("TEST SKU")  # Space not allowed
        
        with pytest.raises(ValidationError, match="SKU can only contain"):
            validate_sku("TEST.SKU")  # Dot not allowed


class TestValidatePrice:
    """Test price validation."""
    
    def test_valid_price_float(self):
        """Test valid price as float."""
        result = validate_price(19.99)
        assert result == Decimal("19.99")
        assert isinstance(result, Decimal)
    
    def test_valid_price_int(self):
        """Test valid price as integer."""
        result = validate_price(20)
        assert result == Decimal("20")
    
    def test_valid_price_string(self):
        """Test valid price as string."""
        result = validate_price("15.50")
        assert result == Decimal("15.50")
    
    def test_valid_price_decimal(self):
        """Test valid price as Decimal."""
        price_decimal = Decimal("25.99")
        result = validate_price(price_decimal)
        assert result == price_decimal
    
    def test_price_zero_raises_error(self):
        """Test zero price raises ValidationError."""
        with pytest.raises(ValidationError, match="Price must be greater than 0"):
            validate_price(0)
        
        with pytest.raises(ValidationError, match="Price must be greater than 0"):
            validate_price("0.00")
    
    def test_price_negative_raises_error(self):
        """Test negative price raises ValidationError."""
        with pytest.raises(ValidationError, match="Price must be greater than 0"):
            validate_price(-10.00)
        
        with pytest.raises(ValidationError, match="Price must be greater than 0"):
            validate_price("-5.99")
    
    def test_price_invalid_format_raises_error(self):
        """Test invalid price format raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid price format"):
            validate_price("not_a_number")
        
        with pytest.raises(ValidationError, match="Price must be a number"):
            validate_price(None)
        
        with pytest.raises(ValidationError, match="Price must be a number"):
            validate_price([])
    
    def test_price_too_many_decimals_raises_error(self):
        """Test price with more than 2 decimal places raises ValidationError."""
        with pytest.raises(ValidationError, match="Price cannot have more than 2 decimal places"):
            validate_price("19.999")
        
        with pytest.raises(ValidationError, match="Price cannot have more than 2 decimal places"):
            validate_price(Decimal("15.123"))


class TestValidateStock:
    """Test stock validation."""
    
    def test_valid_stock(self):
        """Test valid stock values."""
        assert validate_stock(0) == 0
        assert validate_stock(50) == 50
        assert validate_stock(1000) == 1000
    
    def test_stock_string_conversion(self):
        """Test stock string conversion."""
        assert validate_stock("25") == 25
        assert validate_stock("0") == 0
    
    def test_stock_negative_raises_error(self):
        """Test negative stock raises ValidationError."""
        with pytest.raises(ValidationError, match="Stock cannot be negative"):
            validate_stock(-1)
        
        with pytest.raises(ValidationError, match="Stock cannot be negative"):
            validate_stock("-5")
    
    def test_stock_invalid_type_raises_error(self):
        """Test invalid stock type raises ValidationError."""
        with pytest.raises(ValidationError, match="Stock must be an integer"):
            validate_stock("not_a_number")
        
        with pytest.raises(ValidationError, match="Stock must be an integer"):
            validate_stock(15.5)
        
        with pytest.raises(ValidationError, match="Stock must be an integer"):
            validate_stock(None)
    
    def test_stock_too_large_raises_error(self):
        """Test stock exceeding maximum raises ValidationError."""
        with pytest.raises(ValidationError, match="Stock quantity exceeds maximum allowed"):
            validate_stock(1000001)


class TestValidateQuantity:
    """Test quantity validation."""
    
    def test_valid_quantity(self):
        """Test valid quantity values."""
        assert validate_quantity(1) == 1
        assert validate_quantity(50) == 50
        assert validate_quantity(100) == 100
    
    def test_quantity_string_conversion(self):
        """Test quantity string conversion."""
        assert validate_quantity("25") == 25
        assert validate_quantity("1") == 1
    
    def test_quantity_zero_raises_error(self):
        """Test zero quantity raises ValidationError."""
        with pytest.raises(ValidationError, match="Quantity must be greater than 0"):
            validate_quantity(0)
        
        with pytest.raises(ValidationError, match="Quantity must be greater than 0"):
            validate_quantity("0")
    
    def test_quantity_negative_raises_error(self):
        """Test negative quantity raises ValidationError."""
        with pytest.raises(ValidationError, match="Quantity must be greater than 0"):
            validate_quantity(-1)
        
        with pytest.raises(ValidationError, match="Quantity must be greater than 0"):
            validate_quantity("-5")
    
    def test_quantity_invalid_type_raises_error(self):
        """Test invalid quantity type raises ValidationError."""
        with pytest.raises(ValidationError, match="Quantity must be an integer"):
            validate_quantity("not_a_number")
        
        with pytest.raises(ValidationError, match="Quantity must be an integer"):
            validate_quantity(15.5)
        
        with pytest.raises(ValidationError, match="Quantity must be an integer"):
            validate_quantity(None)
    
    def test_quantity_too_large_raises_error(self):
        """Test quantity exceeding maximum raises ValidationError."""
        with pytest.raises(ValidationError, match="Order quantity exceeds maximum allowed"):
            validate_quantity(10001)


class TestValidateProductName:
    """Test product name validation."""
    
    def test_valid_product_name(self):
        """Test valid product names."""
        assert validate_product_name("Widget Alpha") == "Widget Alpha"
        assert validate_product_name("Product-123") == "Product-123"
        assert validate_product_name("Test Product") == "Test Product"
    
    def test_product_name_strips_whitespace(self):
        """Test product name strips whitespace."""
        assert validate_product_name("  Test Product  ") == "Test Product"
        assert validate_product_name("\tWidget\n") == "Widget"
    
    def test_product_name_empty_raises_error(self):
        """Test empty product name raises ValidationError."""
        with pytest.raises(ValidationError, match="Product name must be a non-empty string"):
            validate_product_name("")
        
        with pytest.raises(ValidationError, match="Product name cannot be empty or whitespace only"):
            validate_product_name("   ")
    
    def test_product_name_none_raises_error(self):
        """Test None product name raises ValidationError."""
        with pytest.raises(ValidationError, match="Product name must be a non-empty string"):
            validate_product_name(None)
    
    def test_product_name_too_short_raises_error(self):
        """Test product name shorter than 2 characters raises ValidationError."""
        with pytest.raises(ValidationError, match="Product name must be at least 2 characters long"):
            validate_product_name("A")
    
    def test_product_name_too_long_raises_error(self):
        """Test product name longer than 200 characters raises ValidationError."""
        long_name = "A" * 201
        with pytest.raises(ValidationError, match="Product name cannot exceed 200 characters"):
            validate_product_name(long_name)


class TestValidateEmail:
    """Test email validation."""
    
    def test_valid_email(self):
        """Test valid email addresses."""
        assert validate_email("test@example.com") == "test@example.com"
        assert validate_email("user.name@domain.co.uk") == "user.name@domain.co.uk"
        assert validate_email("test+tag@example.org") == "test+tag@example.org"
    
    def test_email_none_returns_none(self):
        """Test None email returns None."""
        assert validate_email(None) is None
        assert validate_email("") is None
    
    def test_email_converts_to_lowercase(self):
        """Test email is converted to lowercase."""
        assert validate_email("Test@Example.COM") == "test@example.com"
        assert validate_email("USER@DOMAIN.ORG") == "user@domain.org"
    
    def test_email_strips_whitespace(self):
        """Test email strips whitespace."""
        assert validate_email("  test@example.com  ") == "test@example.com"
        assert validate_email("\tuser@domain.org\n") == "user@domain.org"
    
    def test_invalid_email_raises_error(self):
        """Test invalid email format raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("invalid_email")
        
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("@example.com")
        
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("test@")
        
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("test.example.com")
        
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("test@example")  # Missing TLD

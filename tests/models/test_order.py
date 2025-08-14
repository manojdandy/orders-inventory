"""Tests for Order model."""

import pytest
from datetime import datetime

from orders_inventory.models import Order, OrderStatus


class TestOrderModel:
    """Test Order model validation and constraints."""
    
    def test_order_creation_valid(self):
        """Test creating a valid order."""
        order = Order(
            product_id=1,
            quantity=5,
            status=OrderStatus.PENDING
        )
        assert order.product_id == 1
        assert order.quantity == 5
        assert order.status == OrderStatus.PENDING
        assert isinstance(order.created_at, datetime)
    
    def test_quantity_validation_positive(self):
        """Test positive quantity is valid."""
        order = Order(product_id=1, quantity=10)
        assert order.quantity == 10
    
    def test_quantity_validation_zero(self):
        """Test zero quantity raises ValueError."""
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            Order(product_id=1, quantity=0)
    
    def test_quantity_validation_negative(self):
        """Test negative quantity raises ValueError."""
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            Order(product_id=1, quantity=-5)
    
    def test_status_validation_valid_string_lowercase(self):
        """Test valid status string (lowercase) is converted to enum."""
        order = Order(product_id=1, quantity=5, status="pending")
        assert order.status == OrderStatus.PENDING
    
    def test_status_validation_valid_string_uppercase(self):
        """Test valid status string (uppercase) is converted to enum."""
        order = Order(product_id=1, quantity=5, status="PAID")
        assert order.status == OrderStatus.PAID
    
    def test_status_validation_valid_string_mixed_case(self):
        """Test valid status string (mixed case) is converted to enum."""
        order = Order(product_id=1, quantity=5, status="Shipped")
        assert order.status == OrderStatus.SHIPPED
    
    def test_status_validation_invalid_string(self):
        """Test invalid status string raises ValueError."""
        with pytest.raises(ValueError, match="Status must be one of"):
            Order(product_id=1, quantity=5, status="INVALID")
    
    def test_status_validation_enum_value(self):
        """Test passing enum value directly works."""
        order = Order(product_id=1, quantity=5, status=OrderStatus.CANCELED)
        assert order.status == OrderStatus.CANCELED
    
    def test_default_status(self):
        """Test default status is PENDING."""
        order = Order(product_id=1, quantity=5)
        assert order.status == OrderStatus.PENDING
    
    def test_all_status_values(self):
        """Test all valid status values."""
        statuses = [
            OrderStatus.PENDING, 
            OrderStatus.PAID, 
            OrderStatus.SHIPPED, 
            OrderStatus.CANCELED
        ]
        for status in statuses:
            order = Order(product_id=1, quantity=5, status=status)
            assert order.status == status
    
    def test_created_at_auto_set(self):
        """Test created_at is automatically set."""
        before = datetime.utcnow()
        order = Order(product_id=1, quantity=5)
        after = datetime.utcnow()
        
        assert before <= order.created_at <= after
    
    def test_created_at_can_be_set(self):
        """Test created_at can be explicitly set."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        order = Order(
            product_id=1, 
            quantity=5, 
            created_at=custom_time
        )
        assert order.created_at == custom_time


class TestOrderStatus:
    """Test OrderStatus enum."""
    
    def test_order_status_values(self):
        """Test all OrderStatus enum values."""
        assert OrderStatus.PENDING == "PENDING"
        assert OrderStatus.PAID == "PAID"
        assert OrderStatus.SHIPPED == "SHIPPED"
        assert OrderStatus.CANCELED == "CANCELED"
    
    def test_order_status_count(self):
        """Test there are exactly 4 status values."""
        statuses = list(OrderStatus)
        assert len(statuses) == 4
    
    def test_order_status_string_representation(self):
        """Test string representation of status values."""
        assert str(OrderStatus.PENDING) == "PENDING"
        assert str(OrderStatus.PAID) == "PAID"
        assert str(OrderStatus.SHIPPED) == "SHIPPED"
        assert str(OrderStatus.CANCELED) == "CANCELED"

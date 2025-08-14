"""Tests for OrderRepository."""

import pytest
from datetime import datetime, timedelta

from orders_inventory.models import Order, OrderStatus


class TestOrderRepository:
    """Test OrderRepository operations."""
    
    def test_create_order(self, order_repository, sample_order):
        """Test creating an order in database."""
        created = order_repository.create(sample_order)
        
        assert created.id is not None
        assert created.product_id == sample_order.product_id
        assert created.quantity == sample_order.quantity
        assert created.status == OrderStatus.PENDING
        assert isinstance(created.created_at, datetime)
    
    def test_get_by_id(self, order_repository, created_order):
        """Test getting order by ID."""
        retrieved = order_repository.get_by_id(created_order.id)
        assert retrieved is not None
        assert retrieved.product_id == created_order.product_id
        assert retrieved.quantity == created_order.quantity
    
    def test_get_by_id_not_found(self, order_repository):
        """Test getting order by non-existent ID returns None."""
        retrieved = order_repository.get_by_id(99999)
        assert retrieved is None
    
    def test_get_all_empty(self, order_repository):
        """Test getting all orders when repository is empty."""
        orders = order_repository.get_all()
        assert orders == []
    
    def test_get_all_with_orders(self, order_repository, created_product):
        """Test getting all orders."""
        # Create multiple orders
        order1 = Order(product_id=created_product.id, quantity=3)
        order2 = Order(product_id=created_product.id, quantity=7)
        order3 = Order(product_id=created_product.id, quantity=2)
        
        order_repository.create(order1)
        order_repository.create(order2)
        order_repository.create(order3)
        
        orders = order_repository.get_all()
        assert len(orders) == 3
    
    def test_get_by_status(self, order_repository, created_product):
        """Test getting orders by status."""
        # Create orders with different statuses
        pending_order = Order(product_id=created_product.id, quantity=3, status=OrderStatus.PENDING)
        paid_order = Order(product_id=created_product.id, quantity=5, status=OrderStatus.PAID)
        shipped_order = Order(product_id=created_product.id, quantity=2, status=OrderStatus.SHIPPED)
        
        order_repository.create(pending_order)
        order_repository.create(paid_order)
        order_repository.create(shipped_order)
        
        # Test getting pending orders
        pending_orders = order_repository.get_by_status(OrderStatus.PENDING)
        assert len(pending_orders) == 1
        assert pending_orders[0].status == OrderStatus.PENDING
        
        # Test getting paid orders
        paid_orders = order_repository.get_by_status(OrderStatus.PAID)
        assert len(paid_orders) == 1
        assert paid_orders[0].status == OrderStatus.PAID
        
        # Test getting canceled orders (none exist)
        canceled_orders = order_repository.get_by_status(OrderStatus.CANCELED)
        assert len(canceled_orders) == 0
    
    def test_get_by_product_id(self, order_repository, created_products):
        """Test getting orders for a specific product."""
        product1, product2 = created_products[:2]
        
        # Create orders for different products
        order1 = Order(product_id=product1.id, quantity=3)
        order2 = Order(product_id=product1.id, quantity=7)
        order3 = Order(product_id=product2.id, quantity=2)
        
        order_repository.create(order1)
        order_repository.create(order2)
        order_repository.create(order3)
        
        # Get orders for product1
        product1_orders = order_repository.get_by_product_id(product1.id)
        assert len(product1_orders) == 2
        for order in product1_orders:
            assert order.product_id == product1.id
        
        # Get orders for product2
        product2_orders = order_repository.get_by_product_id(product2.id)
        assert len(product2_orders) == 1
        assert product2_orders[0].product_id == product2.id
    
    def test_get_by_date_range(self, order_repository, created_product):
        """Test getting orders within date range."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        # Create order with current time
        order = Order(product_id=created_product.id, quantity=5)
        created_order = order_repository.create(order)
        
        # Search within range that includes the order
        orders_in_range = order_repository.get_by_date_range(yesterday, tomorrow)
        assert len(orders_in_range) == 1
        assert orders_in_range[0].id == created_order.id
        
        # Search outside the range
        past_start = yesterday - timedelta(days=1)
        past_end = yesterday
        orders_outside_range = order_repository.get_by_date_range(past_start, past_end)
        assert len(orders_outside_range) == 0
    
    def test_update_status(self, order_repository, created_order):
        """Test updating order status."""
        order_id = created_order.id
        original_status = created_order.status
        
        # Update to PAID
        updated = order_repository.update_status(order_id, OrderStatus.PAID)
        assert updated is not None
        assert updated.status == OrderStatus.PAID
        assert updated.id == order_id
        
        # Verify the change persists
        retrieved = order_repository.get_by_id(order_id)
        assert retrieved.status == OrderStatus.PAID
    
    def test_update_status_nonexistent_order(self, order_repository):
        """Test updating status of non-existent order returns None."""
        result = order_repository.update_status(99999, OrderStatus.PAID)
        assert result is None
    
    def test_delete_order(self, order_repository, created_order):
        """Test deleting an order."""
        order_id = created_order.id
        
        result = order_repository.delete(order_id)
        assert result is True
        
        # Verify order is deleted
        retrieved = order_repository.get_by_id(order_id)
        assert retrieved is None
    
    def test_delete_nonexistent_order(self, order_repository):
        """Test deleting non-existent order returns False."""
        result = order_repository.delete(99999)
        assert result is False
    
    def test_get_pending_orders(self, order_repository, created_product):
        """Test getting all pending orders."""
        # Create orders with different statuses
        pending1 = Order(product_id=created_product.id, quantity=3, status=OrderStatus.PENDING)
        pending2 = Order(product_id=created_product.id, quantity=5, status=OrderStatus.PENDING)
        paid_order = Order(product_id=created_product.id, quantity=2, status=OrderStatus.PAID)
        
        order_repository.create(pending1)
        order_repository.create(pending2)
        order_repository.create(paid_order)
        
        pending_orders = order_repository.get_pending_orders()
        assert len(pending_orders) == 2
        for order in pending_orders:
            assert order.status == OrderStatus.PENDING
    
    def test_get_recent_orders(self, order_repository, created_product):
        """Test getting recent orders."""
        # Create multiple orders
        orders = []
        for i in range(5):
            order = Order(product_id=created_product.id, quantity=i+1)
            orders.append(order_repository.create(order))
        
        # Get recent orders (default limit 10)
        recent = order_repository.get_recent_orders()
        assert len(recent) == 5
        
        # Orders should be in descending order by created_at (most recent first)
        for i in range(len(recent) - 1):
            assert recent[i].created_at >= recent[i + 1].created_at
        
        # Test with custom limit
        recent_limited = order_repository.get_recent_orders(limit=3)
        assert len(recent_limited) == 3
    
    def test_get_orders_by_quantity_range(self, order_repository, created_product):
        """Test getting orders within quantity range."""
        # Create orders with different quantities
        order1 = Order(product_id=created_product.id, quantity=2)
        order2 = Order(product_id=created_product.id, quantity=5)
        order3 = Order(product_id=created_product.id, quantity=8)
        order4 = Order(product_id=created_product.id, quantity=12)
        
        order_repository.create(order1)
        order_repository.create(order2)
        order_repository.create(order3)
        order_repository.create(order4)
        
        # Range 3-10 should include order2 and order3
        orders_in_range = order_repository.get_orders_by_quantity_range(3, 10)
        assert len(orders_in_range) == 2
        quantities = [order.quantity for order in orders_in_range]
        assert 5 in quantities
        assert 8 in quantities
        
        # Range 1-3 should include order1
        small_orders = order_repository.get_orders_by_quantity_range(1, 3)
        assert len(small_orders) == 1
        assert small_orders[0].quantity == 2
    
    def test_count(self, order_repository, created_product):
        """Test counting orders."""
        # Initially no orders
        assert order_repository.count() == 0
        
        # Create orders
        for i in range(3):
            order = Order(product_id=created_product.id, quantity=i+1)
            order_repository.create(order)
        
        assert order_repository.count() == 3

"""Tests for OrderService."""

import pytest
from decimal import Decimal

from orders_inventory.models import OrderStatus
from orders_inventory.utils.exceptions import (
    OrderNotFoundError,
    InvalidOrderStatusError
)


class TestOrderService:
    """Test OrderService business logic operations."""
    
    def test_get_order_by_id(self, order_service, created_order):
        """Test getting order by ID."""
        retrieved = order_service.get_order_by_id(created_order.id)
        
        assert retrieved is not None
        assert retrieved.id == created_order.id
        assert retrieved.product_id == created_order.product_id
        assert retrieved.quantity == created_order.quantity
    
    def test_get_order_by_id_not_found(self, order_service):
        """Test getting non-existent order by ID returns None."""
        result = order_service.get_order_by_id(99999)
        assert result is None
    
    def test_list_orders_all(self, order_service, created_product):
        """Test listing all orders."""
        # Create multiple orders
        from orders_inventory.models import Order
        order1 = Order(product_id=created_product.id, quantity=3)
        order2 = Order(product_id=created_product.id, quantity=7)
        order3 = Order(product_id=created_product.id, quantity=2)
        
        order_service.order_repo.create(order1)
        order_service.order_repo.create(order2)
        order_service.order_repo.create(order3)
        
        orders = order_service.list_orders()
        assert len(orders) == 3
    
    def test_list_orders_by_status(self, order_service, created_product):
        """Test listing orders filtered by status."""
        from orders_inventory.models import Order
        
        # Create orders with different statuses
        pending = Order(product_id=created_product.id, quantity=3, status=OrderStatus.PENDING)
        paid = Order(product_id=created_product.id, quantity=5, status=OrderStatus.PAID)
        shipped = Order(product_id=created_product.id, quantity=2, status=OrderStatus.SHIPPED)
        
        order_service.order_repo.create(pending)
        order_service.order_repo.create(paid)
        order_service.order_repo.create(shipped)
        
        # Filter by PENDING
        pending_orders = order_service.list_orders(status=OrderStatus.PENDING)
        assert len(pending_orders) == 1
        assert pending_orders[0].status == OrderStatus.PENDING
        
        # Filter by PAID
        paid_orders = order_service.list_orders(status=OrderStatus.PAID)
        assert len(paid_orders) == 1
        assert paid_orders[0].status == OrderStatus.PAID
    
    def test_list_orders_by_product_id(self, order_service, created_products):
        """Test listing orders filtered by product ID."""
        from orders_inventory.models import Order
        product1, product2 = created_products[:2]
        
        # Create orders for different products
        order1 = Order(product_id=product1.id, quantity=3)
        order2 = Order(product_id=product1.id, quantity=7)
        order3 = Order(product_id=product2.id, quantity=2)
        
        order_service.order_repo.create(order1)
        order_service.order_repo.create(order2)
        order_service.order_repo.create(order3)
        
        # Filter by product1
        product1_orders = order_service.list_orders(product_id=product1.id)
        assert len(product1_orders) == 2
        for order in product1_orders:
            assert order.product_id == product1.id
    
    def test_list_orders_with_limit(self, order_service, created_product):
        """Test listing orders with limit."""
        from orders_inventory.models import Order
        
        # Create multiple orders
        for i in range(5):
            order = Order(product_id=created_product.id, quantity=i+1)
            order_service.order_repo.create(order)
        
        # Get with limit
        limited_orders = order_service.list_orders(limit=3)
        assert len(limited_orders) == 3
    
    def test_get_recent_orders(self, order_service, created_product):
        """Test getting recent orders."""
        from orders_inventory.models import Order
        
        # Create multiple orders
        orders = []
        for i in range(5):
            order = Order(product_id=created_product.id, quantity=i+1)
            orders.append(order_service.order_repo.create(order))
        
        recent = order_service.get_recent_orders(limit=3)
        assert len(recent) == 3
        
        # Should be in descending order by created_at
        for i in range(len(recent) - 1):
            assert recent[i].created_at >= recent[i + 1].created_at
    
    def test_mark_as_paid_success(self, order_service, created_order):
        """Test marking order as paid successfully."""
        # Ensure order is in PENDING status
        assert created_order.status == OrderStatus.PENDING
        
        updated = order_service.mark_as_paid(created_order.id)
        
        assert updated.status == OrderStatus.PAID
        assert updated.id == created_order.id
    
    def test_mark_as_paid_order_not_found(self, order_service):
        """Test marking non-existent order as paid raises error."""
        with pytest.raises(OrderNotFoundError, match="Order with ID 99999 not found"):
            order_service.mark_as_paid(99999)
    
    def test_mark_as_paid_invalid_status(self, order_service, created_product):
        """Test marking non-pending order as paid raises error."""
        from orders_inventory.models import Order
        
        # Create order with PAID status
        paid_order = Order(product_id=created_product.id, quantity=5, status=OrderStatus.PAID)
        created = order_service.order_repo.create(paid_order)
        
        with pytest.raises(InvalidOrderStatusError, match="Cannot mark order as paid"):
            order_service.mark_as_paid(created.id)
    
    def test_ship_order_success(self, order_service, created_product):
        """Test shipping order successfully."""
        from orders_inventory.models import Order
        
        # Create order with PAID status
        paid_order = Order(product_id=created_product.id, quantity=5, status=OrderStatus.PAID)
        created = order_service.order_repo.create(paid_order)
        
        updated = order_service.ship_order(created.id)
        
        assert updated.status == OrderStatus.SHIPPED
        assert updated.id == created.id
    
    def test_ship_order_not_found(self, order_service):
        """Test shipping non-existent order raises error."""
        with pytest.raises(OrderNotFoundError, match="Order with ID 99999 not found"):
            order_service.ship_order(99999)
    
    def test_ship_order_invalid_status(self, order_service, created_order):
        """Test shipping non-paid order raises error."""
        # Order is in PENDING status
        assert created_order.status == OrderStatus.PENDING
        
        with pytest.raises(InvalidOrderStatusError, match="Cannot ship order"):
            order_service.ship_order(created_order.id)
    
    def test_cancel_order_pending(self, order_service, created_order, inventory_service):
        """Test canceling pending order restores stock."""
        # Get initial stock
        product = inventory_service.get_product_by_id(created_order.product_id)
        initial_stock = product.stock
        
        updated = order_service.cancel_order(created_order.id)
        
        assert updated.status == OrderStatus.CANCELED
        
        # Check stock was restored
        updated_product = inventory_service.get_product_by_id(created_order.product_id)
        assert updated_product.stock == initial_stock + created_order.quantity
    
    def test_cancel_order_paid(self, order_service, created_product, inventory_service):
        """Test canceling paid order restores stock."""
        from orders_inventory.models import Order
        
        # Get initial stock
        initial_stock = created_product.stock
        
        # Create and pay for order
        paid_order = Order(product_id=created_product.id, quantity=5, status=OrderStatus.PAID)
        created = order_service.order_repo.create(paid_order)
        
        updated = order_service.cancel_order(created.id)
        
        assert updated.status == OrderStatus.CANCELED
        
        # Check stock was restored
        updated_product = inventory_service.get_product_by_id(created_product.id)
        assert updated_product.stock == initial_stock + paid_order.quantity
    
    def test_cancel_order_shipped_fails(self, order_service, created_product):
        """Test canceling shipped order raises error."""
        from orders_inventory.models import Order
        
        # Create shipped order
        shipped_order = Order(product_id=created_product.id, quantity=3, status=OrderStatus.SHIPPED)
        created = order_service.order_repo.create(shipped_order)
        
        with pytest.raises(InvalidOrderStatusError, match="Cannot cancel a shipped order"):
            order_service.cancel_order(created.id)
    
    def test_cancel_order_already_canceled(self, order_service, created_product):
        """Test canceling already canceled order is idempotent."""
        from orders_inventory.models import Order
        
        # Create canceled order
        canceled_order = Order(product_id=created_product.id, quantity=3, status=OrderStatus.CANCELED)
        created = order_service.order_repo.create(canceled_order)
        
        # Should not raise error and return the order
        result = order_service.cancel_order(created.id)
        assert result.status == OrderStatus.CANCELED
    
    def test_cancel_order_not_found(self, order_service):
        """Test canceling non-existent order raises error."""
        with pytest.raises(OrderNotFoundError, match="Order with ID 99999 not found"):
            order_service.cancel_order(99999)
    
    def test_get_order_details(self, order_service, created_order):
        """Test getting detailed order information."""
        details = order_service.get_order_details(created_order.id)
        
        assert details is not None
        assert details["order"]["id"] == created_order.id
        assert details["order"]["quantity"] == created_order.quantity
        assert details["order"]["status"] == created_order.status.value
        
        # Product details should be included
        assert details["product"] is not None
        assert details["product"]["id"] == created_order.product_id
        assert details["product"]["sku"] is not None
        assert details["product"]["name"] is not None
        
        # Total value should be calculated
        assert details["total_value"] is not None
        assert isinstance(details["total_value"], float)
    
    def test_get_order_details_not_found(self, order_service):
        """Test getting details for non-existent order returns None."""
        result = order_service.get_order_details(99999)
        assert result is None
    
    def test_get_orders_summary(self, order_service, created_product):
        """Test getting order statistics summary."""
        from orders_inventory.models import Order
        
        # Create orders with different statuses
        pending = Order(product_id=created_product.id, quantity=3, status=OrderStatus.PENDING)
        paid = Order(product_id=created_product.id, quantity=5, status=OrderStatus.PAID)
        shipped = Order(product_id=created_product.id, quantity=2, status=OrderStatus.SHIPPED)
        canceled = Order(product_id=created_product.id, quantity=1, status=OrderStatus.CANCELED)
        
        order_service.order_repo.create(pending)
        order_service.order_repo.create(paid)
        order_service.order_repo.create(shipped)
        order_service.order_repo.create(canceled)
        
        summary = order_service.get_orders_summary()
        
        assert summary["total_orders"] == 4
        assert summary["status_breakdown"]["PENDING"] == 1
        assert summary["status_breakdown"]["PAID"] == 1
        assert summary["status_breakdown"]["SHIPPED"] == 1
        assert summary["status_breakdown"]["CANCELED"] == 1
        assert summary["total_quantity_ordered"] == 11  # 3+5+2+1
        
        # Should include recent orders
        assert "recent_orders" in summary
        assert len(summary["recent_orders"]) <= 5
    
    def test_validate_order_workflow(self, order_service, created_order):
        """Test order workflow validation."""
        order_id = created_order.id
        
        # Valid transitions from PENDING
        assert order_service.validate_order_workflow(order_id, OrderStatus.PAID) is True
        assert order_service.validate_order_workflow(order_id, OrderStatus.CANCELED) is True
        assert order_service.validate_order_workflow(order_id, OrderStatus.SHIPPED) is False
        
        # Change to PAID and test valid transitions
        order_service.mark_as_paid(order_id)
        assert order_service.validate_order_workflow(order_id, OrderStatus.SHIPPED) is True
        assert order_service.validate_order_workflow(order_id, OrderStatus.CANCELED) is True
        assert order_service.validate_order_workflow(order_id, OrderStatus.PENDING) is False
        
        # Ship the order and test final state
        order_service.ship_order(order_id)
        assert order_service.validate_order_workflow(order_id, OrderStatus.PENDING) is False
        assert order_service.validate_order_workflow(order_id, OrderStatus.PAID) is False
        assert order_service.validate_order_workflow(order_id, OrderStatus.CANCELED) is False
    
    def test_validate_order_workflow_not_found(self, order_service):
        """Test workflow validation for non-existent order returns False."""
        result = order_service.validate_order_workflow(99999, OrderStatus.PAID)
        assert result is False

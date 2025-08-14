"""Sample integration tests for the orders_inventory package.

This module demonstrates basic usage of the orders_inventory system
and serves as integration tests across all components.
"""

import pytest
from decimal import Decimal

from orders_inventory.models import OrderStatus
from orders_inventory.services import InventoryService, OrderService
from orders_inventory.utils.exceptions import InsufficientStockError, DuplicateSKUError


class TestOrdersInventoryIntegration:
    """Integration tests demonstrating end-to-end workflows."""
    
    def test_complete_product_lifecycle(self, inventory_service):
        """Test complete product lifecycle from creation to deletion."""
        # Create product
        product = inventory_service.add_product("LIFE001", "Lifecycle Product", 29.99, 100)
        assert product.sku == "LIFE001"
        assert product.stock == 100
        
        # Update product details
        updated = inventory_service.update_product(
            product.id, 
            name="Updated Lifecycle Product",
            price=34.99
        )
        assert updated.name == "Updated Lifecycle Product"
        assert updated.price == Decimal("34.99")
        
        # Adjust stock
        adjusted = inventory_service.adjust_stock(product.id, -20)
        assert adjusted.stock == 80
        
        # Search for product
        found_products = inventory_service.search_products("Lifecycle")
        assert len(found_products) == 1
        assert found_products[0].id == product.id
    
    def test_complete_order_workflow(self, inventory_service, order_service):
        """Test complete order workflow from creation to shipping."""
        # Create product
        product = inventory_service.add_product("WORK001", "Workflow Product", 15.99, 50)
        
        # Create order
        order = inventory_service.create_order(product.id, 8)
        assert order.status == OrderStatus.PENDING
        assert order.quantity == 8
        
        # Check stock was reduced
        updated_product = inventory_service.get_product_by_id(product.id)
        assert updated_product.stock == 42  # 50 - 8
        
        # Mark order as paid
        paid_order = order_service.mark_as_paid(order.id)
        assert paid_order.status == OrderStatus.PAID
        
        # Ship the order
        shipped_order = order_service.ship_order(order.id)
        assert shipped_order.status == OrderStatus.SHIPPED
        
        # Get order details
        details = order_service.get_order_details(order.id)
        assert details["order"]["status"] == "SHIPPED"
        assert details["product"]["sku"] == "WORK001"
        assert details["total_value"] == float(Decimal("15.99") * 8)
    
    def test_order_cancellation_workflow(self, inventory_service, order_service):
        """Test order cancellation and stock restoration."""
        # Create product
        product = inventory_service.add_product("CANCEL001", "Cancel Product", 20.00, 30)
        
        # Create and pay for order
        order = inventory_service.create_order(product.id, 10)
        paid_order = order_service.mark_as_paid(order.id)
        
        # Check stock after order
        product_after_order = inventory_service.get_product_by_id(product.id)
        assert product_after_order.stock == 20  # 30 - 10
        
        # Cancel the order
        canceled_order = order_service.cancel_order(order.id)
        assert canceled_order.status == OrderStatus.CANCELED
        
        # Check stock was restored
        product_after_cancel = inventory_service.get_product_by_id(product.id)
        assert product_after_cancel.stock == 30  # Back to original
    
    def test_inventory_management_scenarios(self, inventory_service):
        """Test various inventory management scenarios."""
        # Add multiple products
        high_stock = inventory_service.add_product("HIGH001", "High Stock Product", 10.00, 100)
        low_stock = inventory_service.add_product("LOW001", "Low Stock Product", 15.00, 5)
        out_of_stock = inventory_service.add_product("OUT001", "Out of Stock Product", 20.00, 0)
        
        # Test listing with filters
        all_products = inventory_service.list_products()
        assert len(all_products) == 3
        
        in_stock_only = inventory_service.list_products(in_stock_only=True)
        assert len(in_stock_only) == 2  # high_stock and low_stock
        
        low_stock_products = inventory_service.list_products(low_stock_threshold=10)
        assert len(low_stock_products) == 2  # low_stock and out_of_stock
        
        # Test low stock alerts
        alerts = inventory_service.get_low_stock_alert(threshold=10)
        assert len(alerts) == 2
        
        alert_skus = [alert["sku"] for alert in alerts]
        assert "LOW001" in alert_skus
        assert "OUT001" in alert_skus
        assert "HIGH001" not in alert_skus
    
    def test_business_rule_enforcement(self, inventory_service, order_service):
        """Test that business rules are properly enforced."""
        # Test duplicate SKU prevention
        inventory_service.add_product("DUP001", "First Product", 10.00, 50)
        
        with pytest.raises(DuplicateSKUError):
            inventory_service.add_product("DUP001", "Duplicate Product", 15.00, 30)
        
        # Test insufficient stock prevention
        limited_product = inventory_service.add_product("LIMITED001", "Limited Product", 25.00, 3)
        
        with pytest.raises(InsufficientStockError):
            inventory_service.create_order(limited_product.id, 5)
        
        # Test order status workflow validation
        available_product = inventory_service.add_product("AVAIL001", "Available Product", 12.00, 20)
        order = inventory_service.create_order(available_product.id, 5)
        
        # Can't ship pending order
        from orders_inventory.utils.exceptions import InvalidOrderStatusError
        with pytest.raises(InvalidOrderStatusError):
            order_service.ship_order(order.id)
        
        # Must pay first
        order_service.mark_as_paid(order.id)
        shipped_order = order_service.ship_order(order.id)
        
        # Can't cancel shipped order
        with pytest.raises(InvalidOrderStatusError):
            order_service.cancel_order(shipped_order.id)
    
    def test_comprehensive_reporting(self, inventory_service, order_service):
        """Test comprehensive reporting and analytics."""
        # Create diverse product portfolio
        products = [
            ("REPORT001", "Widget A", 10.00, 100),
            ("REPORT002", "Widget B", 15.00, 50),
            ("REPORT003", "Gadget X", 25.00, 20),
            ("REPORT004", "Tool Y", 5.00, 0)  # Out of stock
        ]
        
        created_products = []
        for sku, name, price, stock in products:
            product = inventory_service.add_product(sku, name, price, stock)
            created_products.append(product)
        
        # Create various orders
        orders_data = [
            (0, 10, OrderStatus.PENDING),    # Widget A
            (1, 5, OrderStatus.PAID),        # Widget B
            (2, 3, OrderStatus.SHIPPED),     # Gadget X
            (0, 15, OrderStatus.CANCELED),   # Widget A (canceled)
        ]
        
        for product_idx, quantity, status in orders_data:
            order = inventory_service.create_order(created_products[product_idx].id, quantity)
            if status == OrderStatus.PAID:
                order_service.mark_as_paid(order.id)
            elif status == OrderStatus.SHIPPED:
                order_service.mark_as_paid(order.id)
                order_service.ship_order(order.id)
            elif status == OrderStatus.CANCELED:
                order_service.cancel_order(order.id)
        
        # Get comprehensive reports
        inventory_summary = inventory_service.get_inventory_summary()
        orders_summary = order_service.get_orders_summary()
        
        # Verify inventory summary
        assert inventory_summary["products"]["total"] == 4
        assert inventory_summary["products"]["out_of_stock"] == 1
        assert inventory_summary["orders"]["pending"] == 1
        assert inventory_summary["orders"]["paid"] == 1
        assert inventory_summary["orders"]["shipped"] == 1
        assert inventory_summary["orders"]["canceled"] == 1
        
        # Verify orders summary
        assert orders_summary["total_orders"] == 4
        assert orders_summary["status_breakdown"]["PENDING"] == 1
        assert orders_summary["status_breakdown"]["PAID"] == 1
        assert orders_summary["status_breakdown"]["SHIPPED"] == 1
        assert orders_summary["status_breakdown"]["CANCELED"] == 1
    
    def test_error_handling_and_recovery(self, inventory_service, order_service):
        """Test error handling and system recovery scenarios."""
        # Test graceful handling of non-existent resources
        assert inventory_service.get_product_by_id(99999) is None
        assert inventory_service.get_product_by_sku("NONEXISTENT") is None
        assert order_service.get_order_by_id(99999) is None
        
        # Test updates on non-existent resources
        assert inventory_service.update_product(99999, name="New Name") is None
        assert inventory_service.update_stock(99999, 50) is None
        
        # Test search with no results
        empty_search = inventory_service.search_products("DEFINITELY_NOT_FOUND")
        assert len(empty_search) == 0
        
        # Test workflow validation
        product = inventory_service.add_product("VALID001", "Validation Product", 10.00, 20)
        order = inventory_service.create_order(product.id, 5)
        
        # Test invalid workflow transitions
        assert order_service.validate_order_workflow(order.id, OrderStatus.SHIPPED) is False
        assert order_service.validate_order_workflow(order.id, OrderStatus.PAID) is True
        assert order_service.validate_order_workflow(99999, OrderStatus.PAID) is False

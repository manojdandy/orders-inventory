"""Tests for InventoryService."""

import pytest
from decimal import Decimal

from orders_inventory.models import OrderStatus
from orders_inventory.utils.exceptions import (
    DuplicateSKUError, 
    ProductNotFoundError, 
    InsufficientStockError
)


class TestInventoryService:
    """Test InventoryService business logic operations."""
    
    def test_add_product_success(self, inventory_service):
        """Test adding a product successfully."""
        product = inventory_service.add_product("NEW001", "New Product", 25.99, 30)
        
        assert product.sku == "NEW001"
        assert product.name == "New Product"
        assert product.price == Decimal("25.99")
        assert product.stock == 30
        assert product.id is not None
    
    def test_add_product_duplicate_sku(self, inventory_service):
        """Test adding product with duplicate SKU raises error."""
        inventory_service.add_product("DUP001", "First Product", 25.99, 30)
        
        with pytest.raises(DuplicateSKUError, match="Product with SKU 'DUP001' already exists"):
            inventory_service.add_product("DUP001", "Second Product", 35.99, 20)
    
    def test_update_product_success(self, inventory_service):
        """Test updating product details."""
        product = inventory_service.add_product("UPD001", "Original Product", 15.99, 25)
        
        updated = inventory_service.update_product(
            product.id,
            name="Updated Product",
            price=19.99,
            stock=50
        )
        
        assert updated is not None
        assert updated.name == "Updated Product"
        assert updated.price == Decimal("19.99")
        assert updated.stock == 50
        assert updated.sku == "UPD001"  # SKU should remain unchanged
    
    def test_update_product_not_found(self, inventory_service):
        """Test updating non-existent product returns None."""
        result = inventory_service.update_product(99999, name="New Name")
        assert result is None
    
    def test_update_stock_success(self, inventory_service):
        """Test updating product stock."""
        product = inventory_service.add_product("STK001", "Stock Product", 10.00, 25)
        
        updated = inventory_service.update_stock(product.id, 100)
        
        assert updated is not None
        assert updated.stock == 100
        assert updated.name == "Stock Product"  # Other fields unchanged
    
    def test_update_stock_not_found(self, inventory_service):
        """Test updating stock of non-existent product returns None."""
        result = inventory_service.update_stock(99999, 50)
        assert result is None
    
    def test_adjust_stock_positive(self, inventory_service):
        """Test adjusting stock with positive delta."""
        product = inventory_service.add_product("ADJ001", "Adjust Product", 10.00, 20)
        
        updated = inventory_service.adjust_stock(product.id, 15)
        
        assert updated is not None
        assert updated.stock == 35  # 20 + 15
    
    def test_adjust_stock_negative(self, inventory_service):
        """Test adjusting stock with negative delta."""
        product = inventory_service.add_product("ADJ002", "Adjust Product", 10.00, 20)
        
        updated = inventory_service.adjust_stock(product.id, -5)
        
        assert updated is not None
        assert updated.stock == 15  # 20 - 5
    
    def test_adjust_stock_negative_floor_zero(self, inventory_service):
        """Test adjusting stock with large negative delta floors at zero."""
        product = inventory_service.add_product("ADJ003", "Adjust Product", 10.00, 20)
        
        updated = inventory_service.adjust_stock(product.id, -30)
        
        assert updated is not None
        assert updated.stock == 0  # Floor at 0, not -10
    
    def test_adjust_stock_not_found(self, inventory_service):
        """Test adjusting stock of non-existent product returns None."""
        result = inventory_service.adjust_stock(99999, 10)
        assert result is None
    
    def test_get_product_by_sku(self, inventory_service):
        """Test getting product by SKU."""
        created = inventory_service.add_product("GET001", "Get Product", 15.00, 30)
        
        retrieved = inventory_service.get_product_by_sku("GET001")
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.sku == "GET001"
    
    def test_get_product_by_sku_not_found(self, inventory_service):
        """Test getting non-existent product by SKU returns None."""
        result = inventory_service.get_product_by_sku("NONEXISTENT")
        assert result is None
    
    def test_get_product_by_id(self, inventory_service):
        """Test getting product by ID."""
        created = inventory_service.add_product("GET002", "Get Product", 15.00, 30)
        
        retrieved = inventory_service.get_product_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.sku == "GET002"
        assert retrieved.name == "Get Product"
    
    def test_get_product_by_id_not_found(self, inventory_service):
        """Test getting non-existent product by ID returns None."""
        result = inventory_service.get_product_by_id(99999)
        assert result is None
    
    def test_list_products_all(self, inventory_service):
        """Test listing all products."""
        inventory_service.add_product("LIST001", "Product 1", 10.00, 50)
        inventory_service.add_product("LIST002", "Product 2", 15.00, 0)
        inventory_service.add_product("LIST003", "Product 3", 20.00, 5)
        
        products = inventory_service.list_products()
        
        assert len(products) == 3
        skus = [p.sku for p in products]
        assert "LIST001" in skus
        assert "LIST002" in skus
        assert "LIST003" in skus
    
    def test_list_products_in_stock_only(self, inventory_service):
        """Test listing only products in stock."""
        inventory_service.add_product("LIST004", "In Stock", 10.00, 50)
        inventory_service.add_product("LIST005", "Out of Stock", 15.00, 0)
        inventory_service.add_product("LIST006", "In Stock Too", 20.00, 5)
        
        products = inventory_service.list_products(in_stock_only=True)
        
        assert len(products) == 2
        for product in products:
            assert product.stock > 0
    
    def test_list_products_low_stock(self, inventory_service):
        """Test listing products with low stock."""
        inventory_service.add_product("LIST007", "High Stock", 10.00, 50)
        inventory_service.add_product("LIST008", "Low Stock", 15.00, 5)
        inventory_service.add_product("LIST009", "Out of Stock", 20.00, 0)
        
        products = inventory_service.list_products(low_stock_threshold=10)
        
        assert len(products) == 2  # Both low stock and out of stock
        for product in products:
            assert product.stock < 10
    
    def test_search_products(self, inventory_service):
        """Test searching products by name pattern."""
        inventory_service.add_product("SEARCH001", "Widget Alpha", 10.00, 50)
        inventory_service.add_product("SEARCH002", "Widget Beta", 15.00, 30)
        inventory_service.add_product("SEARCH003", "Gadget Gamma", 20.00, 25)
        
        # Search for "Widget"
        widgets = inventory_service.search_products("Widget")
        assert len(widgets) == 2
        
        # Search for "Alpha"
        alpha_products = inventory_service.search_products("Alpha")
        assert len(alpha_products) == 1
        assert alpha_products[0].name == "Widget Alpha"
        
        # Search for non-existent pattern
        none_found = inventory_service.search_products("Nonexistent")
        assert len(none_found) == 0
    
    def test_create_order_success(self, inventory_service):
        """Test creating order successfully."""
        product = inventory_service.add_product("ORDER001", "Order Product", 15.00, 50)
        
        order = inventory_service.create_order(product.id, 10)
        
        assert order.product_id == product.id
        assert order.quantity == 10
        assert order.status == OrderStatus.PENDING
        
        # Check stock was reduced
        updated_product = inventory_service.get_product_by_id(product.id)
        assert updated_product.stock == 40  # 50 - 10
    
    def test_create_order_product_not_found(self, inventory_service):
        """Test creating order for non-existent product raises error."""
        with pytest.raises(ProductNotFoundError, match="Product with ID 99999 not found"):
            inventory_service.create_order(99999, 5)
    
    def test_create_order_insufficient_stock(self, inventory_service):
        """Test creating order with insufficient stock raises error."""
        product = inventory_service.add_product("ORDER002", "Low Stock Product", 10.00, 5)
        
        with pytest.raises(InsufficientStockError, match="Insufficient stock"):
            inventory_service.create_order(product.id, 10)
    
    def test_get_inventory_summary(self, inventory_service):
        """Test getting comprehensive inventory summary."""
        # Add products
        product1 = inventory_service.add_product("SUM001", "Product 1", 10.00, 20)
        product2 = inventory_service.add_product("SUM002", "Product 2", 5.00, 0)  # Out of stock
        product3 = inventory_service.add_product("SUM003", "Product 3", 15.00, 5)  # Low stock
        
        # Create orders
        order1 = inventory_service.create_order(product1.id, 5)
        order2 = inventory_service.create_order(product3.id, 2)
        
        summary = inventory_service.get_inventory_summary()
        
        # Product statistics
        assert summary["products"]["total"] == 3
        assert summary["products"]["in_stock"] == 2  # product1 and product3 still have stock
        assert summary["products"]["out_of_stock"] == 1  # product2
        assert summary["products"]["low_stock_count"] == 1  # product3 (3 remaining < 10)
        assert summary["products"]["total_stock_quantity"] == 18  # 15 + 0 + 3
        assert summary["products"]["total_stock_value"] == 195.0  # (15*10) + (0*5) + (3*15)
        
        # Order statistics
        assert summary["orders"]["total"] == 2
        assert summary["orders"]["pending"] == 2
        assert summary["orders"]["paid"] == 0
        assert summary["orders"]["shipped"] == 0
        assert summary["orders"]["canceled"] == 0
        assert summary["orders"]["total_quantity_ordered"] == 7  # 5 + 2
    
    def test_get_low_stock_alert(self, inventory_service):
        """Test getting low stock alerts."""
        # Add products with different stock levels
        inventory_service.add_product("ALERT001", "High Stock", 10.00, 50)
        inventory_service.add_product("ALERT002", "Low Stock", 15.00, 5)
        inventory_service.add_product("ALERT003", "Out of Stock", 20.00, 0)
        inventory_service.add_product("ALERT004", "Critical Stock", 25.00, 2)
        
        alerts = inventory_service.get_low_stock_alert(threshold=10)
        
        assert len(alerts) == 3  # All except "High Stock"
        
        # Check alert structure
        alert_skus = [alert["sku"] for alert in alerts]
        assert "ALERT002" in alert_skus
        assert "ALERT003" in alert_skus
        assert "ALERT004" in alert_skus
        assert "ALERT001" not in alert_skus
        
        # Check specific alert details
        low_stock_alert = next(alert for alert in alerts if alert["sku"] == "ALERT002")
        assert low_stock_alert["current_stock"] == 5
        assert low_stock_alert["threshold"] == 10
        assert low_stock_alert["shortage"] == 5  # 10 - 5
        
        out_of_stock_alert = next(alert for alert in alerts if alert["sku"] == "ALERT003")
        assert out_of_stock_alert["current_stock"] == 0
        assert out_of_stock_alert["shortage"] == 10  # 10 - 0
    
    def test_get_low_stock_alert_custom_threshold(self, inventory_service):
        """Test low stock alerts with custom threshold."""
        inventory_service.add_product("THRESH001", "Product", 10.00, 15)
        
        # With threshold 20, should trigger alert
        alerts_high = inventory_service.get_low_stock_alert(threshold=20)
        assert len(alerts_high) == 1
        
        # With threshold 10, should not trigger alert
        alerts_low = inventory_service.get_low_stock_alert(threshold=10)
        assert len(alerts_low) == 0

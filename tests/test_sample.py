"""Sample tests for the orders_inventory package."""

import pytest
from orders_inventory.inventory import InventoryManager


class TestInventoryManager:
    """Test cases for InventoryManager class."""
    
    def test_add_item(self):
        """Test that add_item works correctly."""
        manager = InventoryManager()
        
        # Add a new item
        manager.add_item("item1", "Test Item", 10, 19.99)
        
        # Check that item was added
        items = manager.list_items()
        assert len(items) == 1
        assert items[0]["id"] == "item1"
        assert items[0]["name"] == "Test Item"
        assert items[0]["quantity"] == 10
        assert items[0]["price"] == 19.99
    
    def test_add_existing_item_increases_quantity(self):
        """Test that adding an existing item increases its quantity."""
        manager = InventoryManager()
        
        # Add item twice
        manager.add_item("item1", "Test Item", 5, 10.0)
        manager.add_item("item1", "Test Item", 3, 10.0)
        
        # Check quantity was increased
        item = manager.get_item("item1")
        assert item["quantity"] == 8
    
    def test_list_items_empty_inventory(self):
        """Test that list_items returns empty list for empty inventory."""
        manager = InventoryManager()
        items = manager.list_items()
        assert items == []
    
    def test_get_item_not_found(self):
        """Test that get_item returns None for non-existent item."""
        manager = InventoryManager()
        item = manager.get_item("nonexistent")
        assert item is None
    
    def test_remove_item(self):
        """Test that remove_item works correctly."""
        manager = InventoryManager()
        
        # Add and then remove item
        manager.add_item("item1", "Test Item", 10, 19.99)
        result = manager.remove_item("item1")
        
        assert result is True
        assert manager.get_item("item1") is None
    
    def test_remove_partial_quantity(self):
        """Test removing partial quantity of an item."""
        manager = InventoryManager()
        
        # Add item and remove partial quantity
        manager.add_item("item1", "Test Item", 10, 19.99)
        result = manager.remove_item("item1", 3)
        
        assert result is True
        item = manager.get_item("item1")
        assert item["quantity"] == 7
    
    def test_remove_nonexistent_item(self):
        """Test that removing non-existent item returns False."""
        manager = InventoryManager()
        result = manager.remove_item("nonexistent")
        assert result is False

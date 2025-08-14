"""Inventory management module."""

from typing import Dict, List, Any


class InventoryManager:
    """A simple inventory management system."""
    
    def __init__(self):
        """Initialize the inventory manager with an empty inventory."""
        self._items: Dict[str, Dict[str, Any]] = {}
    
    def add_item(self, item_id: str, name: str, quantity: int, price: float = 0.0) -> None:
        """
        Add an item to the inventory.
        
        Args:
            item_id (str): Unique identifier for the item
            name (str): Name of the item
            quantity (int): Quantity of the item
            price (float): Price per unit of the item
        """
        if item_id in self._items:
            # If item exists, update quantity
            self._items[item_id]["quantity"] += quantity
        else:
            # Add new item
            self._items[item_id] = {
                "name": name,
                "quantity": quantity,
                "price": price
            }
    
    def list_items(self) -> List[Dict[str, Any]]:
        """
        Get a list of all items in the inventory.
        
        Returns:
            List[Dict[str, Any]]: List of items with their details
        """
        items = []
        for item_id, details in self._items.items():
            item = {"id": item_id}
            item.update(details)
            items.append(item)
        return items
    
    def get_item(self, item_id: str) -> Dict[str, Any] | None:
        """
        Get details of a specific item.
        
        Args:
            item_id (str): Unique identifier for the item
            
        Returns:
            Dict[str, Any] | None: Item details or None if not found
        """
        if item_id in self._items:
            item = {"id": item_id}
            item.update(self._items[item_id])
            return item
        return None
    
    def remove_item(self, item_id: str, quantity: int = None) -> bool:
        """
        Remove an item or reduce its quantity.
        
        Args:
            item_id (str): Unique identifier for the item
            quantity (int, optional): Quantity to remove. If None, removes entire item.
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        if item_id not in self._items:
            return False
        
        if quantity is None:
            # Remove entire item
            del self._items[item_id]
            return True
        
        current_quantity = self._items[item_id]["quantity"]
        if quantity >= current_quantity:
            # Remove entire item if quantity to remove >= current quantity
            del self._items[item_id]
        else:
            # Reduce quantity
            self._items[item_id]["quantity"] -= quantity
        
        return True

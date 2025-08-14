"""Inventory management service with business logic."""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlmodel import Session

from ..models import Product, Order, OrderStatus
from ..repositories import ProductRepository, OrderRepository
from ..utils.exceptions import InsufficientStockError, ProductNotFoundError, DuplicateSKUError


class InventoryService:
    """High-level inventory management service."""
    
    def __init__(self, session: Session):
        """Initialize service with database session.
        
        Args:
            session: Database session
        """
        self.session = session
        self.product_repo = ProductRepository(session)
        self.order_repo = OrderRepository(session)
    
    def add_product(self, sku: str, name: str, price: float, stock: int) -> Product:
        """Add a new product to inventory.
        
        Args:
            sku: Product SKU
            name: Product name
            price: Product price
            stock: Initial stock quantity
            
        Returns:
            Created product
            
        Raises:
            DuplicateSKUError: If SKU already exists
        """
        # Check if SKU already exists
        existing = self.product_repo.get_by_sku(sku)
        if existing:
            raise DuplicateSKUError(f"Product with SKU '{sku}' already exists")
        
        product = Product(
            sku=sku, 
            name=name, 
            price=Decimal(str(price)), 
            stock=stock
        )
        return self.product_repo.create(product)
    
    def update_product(self, product_id: int, **kwargs) -> Optional[Product]:
        """Update product details.
        
        Args:
            product_id: Product ID
            **kwargs: Fields to update
            
        Returns:
            Updated product or None if not found
        """
        product = self.product_repo.get_by_id(product_id)
        if not product:
            return None
        
        for key, value in kwargs.items():
            if hasattr(product, key):
                if key == 'price':
                    value = Decimal(str(value))
                setattr(product, key, value)
        
        return self.product_repo.update(product)
    
    def update_stock(self, product_id: int, new_stock: int) -> Optional[Product]:
        """Update product stock.
        
        Args:
            product_id: Product ID
            new_stock: New stock quantity
            
        Returns:
            Updated product or None if not found
        """
        return self.update_product(product_id, stock=new_stock)
    
    def adjust_stock(self, product_id: int, adjustment: int) -> Optional[Product]:
        """Adjust product stock by a delta amount.
        
        Args:
            product_id: Product ID
            adjustment: Stock adjustment (positive or negative)
            
        Returns:
            Updated product or None if not found
        """
        product = self.product_repo.get_by_id(product_id)
        if product:
            new_stock = max(0, product.stock + adjustment)
            return self.update_stock(product_id, new_stock)
        return None
    
    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        return self.product_repo.get_by_sku(sku)
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        return self.product_repo.get_by_id(product_id)
    
    def list_products(self, 
                     in_stock_only: bool = False,
                     low_stock_threshold: Optional[int] = None) -> List[Product]:
        """List products with optional filters.
        
        Args:
            in_stock_only: If True, only return products with stock > 0
            low_stock_threshold: If provided, only return products below this threshold
            
        Returns:
            List of products
        """
        if low_stock_threshold is not None:
            return self.product_repo.get_low_stock(low_stock_threshold)
        elif in_stock_only:
            return self.product_repo.get_in_stock()
        else:
            return self.product_repo.get_all()
    
    def search_products(self, name_pattern: str) -> List[Product]:
        """Search products by name pattern."""
        return self.product_repo.search_by_name(name_pattern)
    
    def create_order(self, product_id: int, quantity: int) -> Order:
        """Create a new order and reserve stock.
        
        Args:
            product_id: Product ID
            quantity: Order quantity
            
        Returns:
            Created order
            
        Raises:
            ProductNotFoundError: If product doesn't exist
            InsufficientStockError: If not enough stock available
        """
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")
        
        if product.stock < quantity:
            raise InsufficientStockError(
                f"Insufficient stock. Available: {product.stock}, Requested: {quantity}"
            )
        
        # Create order
        order = Order(product_id=product_id, quantity=quantity)
        order = self.order_repo.create(order)
        
        # Reserve stock
        product.stock -= quantity
        self.product_repo.update(product)
        
        return order
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get comprehensive inventory summary.
        
        Returns:
            Dictionary with inventory statistics
        """
        products = self.product_repo.get_all()
        orders = self.order_repo.get_all()
        
        # Product statistics
        total_products = len(products)
        in_stock_products = len(self.product_repo.get_in_stock())
        out_of_stock_products = len(self.product_repo.get_out_of_stock())
        low_stock_products = len(self.product_repo.get_low_stock())
        
        total_stock_quantity = sum(p.stock for p in products)
        total_stock_value = sum(p.price * p.stock for p in products)
        
        # Order statistics
        pending_orders = len(self.order_repo.get_by_status(OrderStatus.PENDING))
        paid_orders = len(self.order_repo.get_by_status(OrderStatus.PAID))
        shipped_orders = len(self.order_repo.get_by_status(OrderStatus.SHIPPED))
        canceled_orders = len(self.order_repo.get_by_status(OrderStatus.CANCELED))
        
        total_orders = len(orders)
        total_order_quantity = sum(o.quantity for o in orders)
        
        return {
            "products": {
                "total": total_products,
                "in_stock": in_stock_products,
                "out_of_stock": out_of_stock_products,
                "low_stock_count": low_stock_products,
                "total_stock_quantity": total_stock_quantity,
                "total_stock_value": float(total_stock_value)
            },
            "orders": {
                "total": total_orders,
                "pending": pending_orders,
                "paid": paid_orders,
                "shipped": shipped_orders,
                "canceled": canceled_orders,
                "total_quantity_ordered": total_order_quantity
            }
        }
    
    def get_low_stock_alert(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """Get low stock alerts with product details.
        
        Args:
            threshold: Stock threshold for alert
            
        Returns:
            List of low stock alerts
        """
        low_stock_products = self.product_repo.get_low_stock(threshold)
        return [
            {
                "product_id": p.id,
                "sku": p.sku,
                "name": p.name,
                "current_stock": p.stock,
                "threshold": threshold,
                "shortage": max(0, threshold - p.stock)
            }
            for p in low_stock_products
        ]

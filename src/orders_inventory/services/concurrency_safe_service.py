"""Concurrency-safe order creation service."""

from typing import Optional
from sqlmodel import Session, text
from sqlalchemy.exc import IntegrityError

from ..models import Product, Order, OrderStatus
from ..repositories import ProductRepository, OrderRepository
from ..utils.exceptions import (
    ProductNotFoundError,
    InsufficientStockError,
    ConcurrentModificationError
)


class ConcurrentModificationError(Exception):
    """Raised when a concurrent modification is detected."""
    pass


class ConcurrencySafeOrderService:
    """Order service with concurrency protection."""
    
    def __init__(self, session: Session):
        self.session = session
        self.product_repo = ProductRepository(session)
        self.order_repo = OrderRepository(session)
    
    def create_order_atomic_sqlite(self, product_id: int, quantity: int) -> Order:
        """
        Create order with atomic stock update for SQLite.
        
        This method prevents race conditions by using a single atomic UPDATE
        statement that checks stock availability and reduces it in one operation.
        """
        try:
            # Atomic UPDATE: only succeeds if stock is sufficient
            result = self.session.execute(
                text("""
                    UPDATE products 
                    SET stock = stock - :quantity 
                    WHERE id = :product_id AND stock >= :quantity
                """),
                {"quantity": quantity, "product_id": product_id}
            )
            
            # Check if update affected any rows
            if result.rowcount == 0:
                # Either product doesn't exist or insufficient stock
                product = self.product_repo.get_by_id(product_id)
                if not product:
                    raise ProductNotFoundError(f"Product with ID {product_id} not found")
                else:
                    raise InsufficientStockError(
                        f"Insufficient stock. Available: {product.stock}, Requested: {quantity}"
                    )
            
            # Stock successfully reduced, now create order
            order = Order(product_id=product_id, quantity=quantity)
            created_order = self.order_repo.create(order)
            
            # Commit the transaction
            self.session.commit()
            return created_order
            
        except Exception:
            # Rollback on any error
            self.session.rollback()
            raise
    
    def create_order_with_optimistic_locking(self, product_id: int, quantity: int, max_retries: int = 3) -> Order:
        """
        Create order with optimistic locking and retry mechanism.
        
        This method handles concurrent modifications by detecting conflicts
        and retrying the operation up to max_retries times.
        """
        for attempt in range(max_retries):
            try:
                # Get product with current version
                product = self.product_repo.get_by_id(product_id)
                if not product:
                    raise ProductNotFoundError(f"Product with ID {product_id} not found")
                
                if product.stock < quantity:
                    raise InsufficientStockError(
                        f"Insufficient stock. Available: {product.stock}, Requested: {quantity}"
                    )
                
                # Store original version for optimistic locking
                original_version = getattr(product, 'version', 0)
                
                # Try to update with version check
                result = self.session.execute(
                    text("""
                        UPDATE products 
                        SET stock = stock - :quantity,
                            version = COALESCE(version, 0) + 1
                        WHERE id = :product_id 
                        AND stock >= :quantity
                        AND COALESCE(version, 0) = :expected_version
                    """),
                    {
                        "quantity": quantity, 
                        "product_id": product_id,
                        "expected_version": original_version
                    }
                )
                
                if result.rowcount == 0:
                    if attempt < max_retries - 1:
                        # Retry on concurrent modification
                        self.session.rollback()
                        continue
                    else:
                        # Final attempt failed
                        current_product = self.product_repo.get_by_id(product_id)
                        if current_product and current_product.stock < quantity:
                            raise InsufficientStockError(
                                f"Insufficient stock after retries. Available: {current_product.stock}, Requested: {quantity}"
                            )
                        else:
                            raise ConcurrentModificationError(
                                f"Unable to complete order after {max_retries} attempts due to concurrent modifications"
                            )
                
                # Success! Create the order
                order = Order(product_id=product_id, quantity=quantity)
                created_order = self.order_repo.create(order)
                self.session.commit()
                return created_order
                
            except (ProductNotFoundError, InsufficientStockError):
                # Don't retry these business logic errors
                self.session.rollback()
                raise
            except Exception as e:
                self.session.rollback()
                if attempt < max_retries - 1:
                    continue
                raise
        
        # Should never reach here
        raise ConcurrentModificationError("Max retries exceeded")
    
    def create_order_with_row_locking(self, product_id: int, quantity: int) -> Order:
        """
        Create order with explicit row locking (PostgreSQL/MySQL).
        
        Note: This requires a database that supports SELECT FOR UPDATE.
        SQLite doesn't support this, so it will fall back to table-level locking.
        """
        try:
            # Start explicit transaction
            with self.session.begin():
                # Lock the product row (PostgreSQL/MySQL)
                from sqlmodel import select
                
                # This will lock the row in databases that support it
                product = self.session.execute(
                    select(Product)
                    .where(Product.id == product_id)
                    .with_for_update()
                ).scalar_one_or_none()
                
                if not product:
                    raise ProductNotFoundError(f"Product with ID {product_id} not found")
                
                if product.stock < quantity:
                    raise InsufficientStockError(
                        f"Insufficient stock. Available: {product.stock}, Requested: {quantity}"
                    )
                
                # Update stock
                product.stock -= quantity
                self.session.add(product)
                
                # Create order
                order = Order(product_id=product_id, quantity=quantity)
                created_order = self.order_repo.create(order)
                
                # Transaction commits automatically
                return created_order
                
        except Exception:
            self.session.rollback()
            raise
    
    def get_concurrent_safe_stock(self, product_id: int) -> int:
        """
        Get current stock with read consistency.
        
        This method ensures you get the most up-to-date stock value,
        accounting for any concurrent modifications.
        """
        result = self.session.execute(
            text("SELECT stock FROM products WHERE id = :product_id"),
            {"product_id": product_id}
        )
        row = result.fetchone()
        return row[0] if row else 0


# Error response for concurrent modification
CONCURRENT_MODIFICATION_RESPONSE = {
    "error": "ConcurrentModificationError",
    "details": [
        {
            "type": "ConcurrentModificationError",
            "message": "Unable to complete order due to concurrent modifications. Please try again.",
            "field": null
        }
    ],
    "timestamp": "2023-12-01T15:00:00.000000"
}

# Production database configuration recommendations
DATABASE_CONFIGS = {
    "sqlite": {
        "connection_string": "sqlite:///orders_inventory.db",
        "isolation_level": "SERIALIZABLE",  # Highest isolation for SQLite
        "timeout": 30,
        "note": "Use atomic UPDATE operations for concurrency safety"
    },
    "postgresql": {
        "connection_string": "postgresql://user:pass@localhost/orders_inventory",
        "isolation_level": "READ_COMMITTED",  # Default for PostgreSQL
        "pool_size": 10,
        "note": "Use SELECT FOR UPDATE for pessimistic locking"
    },
    "mysql": {
        "connection_string": "mysql://user:pass@localhost/orders_inventory",
        "isolation_level": "READ_COMMITTED",
        "pool_size": 10,
        "note": "Use SELECT FOR UPDATE for pessimistic locking"
    }
}

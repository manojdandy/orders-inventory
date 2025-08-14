"""Order management service with business logic."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import Session

from ..models import Order, OrderStatus, Product
from ..repositories import OrderRepository, ProductRepository
from ..utils.exceptions import OrderNotFoundError, InvalidOrderStatusError


class OrderService:
    """High-level order management service."""
    
    def __init__(self, session: Session):
        """Initialize service with database session.
        
        Args:
            session: Database session
        """
        self.session = session
        self.order_repo = OrderRepository(session)
        self.product_repo = ProductRepository(session)
    
    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID."""
        return self.order_repo.get_by_id(order_id)
    
    def list_orders(self, 
                   status: Optional[OrderStatus] = None,
                   product_id: Optional[int] = None,
                   limit: Optional[int] = None) -> List[Order]:
        """List orders with optional filters.
        
        Args:
            status: Filter by order status
            product_id: Filter by product ID
            limit: Limit number of results
            
        Returns:
            List of orders
        """
        if status:
            orders = self.order_repo.get_by_status(status)
        elif product_id:
            orders = self.order_repo.get_by_product_id(product_id)
        else:
            orders = self.order_repo.get_all()
        
        if limit:
            orders = orders[:limit]
        
        return orders
    
    def get_recent_orders(self, limit: int = 10) -> List[Order]:
        """Get recent orders."""
        return self.order_repo.get_recent_orders(limit)
    
    def mark_as_paid(self, order_id: int) -> Order:
        """Mark order as paid.
        
        Args:
            order_id: Order ID
            
        Returns:
            Updated order
            
        Raises:
            OrderNotFoundError: If order doesn't exist
            InvalidOrderStatusError: If order is not in PENDING status
        """
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order with ID {order_id} not found")
        
        if order.status != OrderStatus.PENDING:
            raise InvalidOrderStatusError(
                f"Cannot mark order as paid. Current status: {order.status}. "
                f"Order must be PENDING to mark as PAID."
            )
        
        return self.order_repo.update_status(order_id, OrderStatus.PAID)
    
    def ship_order(self, order_id: int) -> Order:
        """Mark order as shipped.
        
        Args:
            order_id: Order ID
            
        Returns:
            Updated order
            
        Raises:
            OrderNotFoundError: If order doesn't exist
            InvalidOrderStatusError: If order is not in PAID status
        """
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order with ID {order_id} not found")
        
        if order.status != OrderStatus.PAID:
            raise InvalidOrderStatusError(
                f"Cannot ship order. Current status: {order.status}. "
                f"Order must be PAID to ship."
            )
        
        return self.order_repo.update_status(order_id, OrderStatus.SHIPPED)
    
    def cancel_order(self, order_id: int) -> Order:
        """Cancel an order and restore stock.
        
        Args:
            order_id: Order ID
            
        Returns:
            Updated order
            
        Raises:
            OrderNotFoundError: If order doesn't exist
            InvalidOrderStatusError: If order is already shipped
        """
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order with ID {order_id} not found")
        
        if order.status == OrderStatus.SHIPPED:
            raise InvalidOrderStatusError("Cannot cancel a shipped order")
        
        if order.status == OrderStatus.CANCELED:
            return order  # Already canceled
        
        # Restore stock if order was paid or pending
        if order.status in [OrderStatus.PENDING, OrderStatus.PAID]:
            product = self.product_repo.get_by_id(order.product_id)
            if product:
                product.stock += order.quantity
                self.product_repo.update(product)
        
        return self.order_repo.update_status(order_id, OrderStatus.CANCELED)
    
    def get_order_details(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed order information including product details.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order details with product information or None if not found
        """
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return None
        
        product = self.product_repo.get_by_id(order.product_id)
        
        return {
            "order": {
                "id": order.id,
                "quantity": order.quantity,
                "status": order.status.value,
                "created_at": order.created_at.isoformat()
            },
            "product": {
                "id": product.id if product else None,
                "sku": product.sku if product else None,
                "name": product.name if product else None,
                "price": float(product.price) if product else None,
                "current_stock": product.stock if product else None
            } if product else None,
            "total_value": float(product.price * order.quantity) if product else None
        }
    
    def get_orders_summary(self) -> Dict[str, Any]:
        """Get order statistics summary.
        
        Returns:
            Dictionary with order statistics
        """
        all_orders = self.order_repo.get_all()
        
        # Count by status
        status_counts = {status.value: 0 for status in OrderStatus}
        total_quantity = 0
        total_value = 0.0
        
        for order in all_orders:
            status_counts[order.status.value] += 1
            total_quantity += order.quantity
            
            # Calculate value if product exists
            product = self.product_repo.get_by_id(order.product_id)
            if product:
                total_value += float(product.price * order.quantity)
        
        # Recent activity
        recent_orders = self.order_repo.get_recent_orders(5)
        
        return {
            "total_orders": len(all_orders),
            "status_breakdown": status_counts,
            "total_quantity_ordered": total_quantity,
            "total_order_value": total_value,
            "recent_orders": [
                {
                    "id": order.id,
                    "product_id": order.product_id,
                    "quantity": order.quantity,
                    "status": order.status.value,
                    "created_at": order.created_at.isoformat()
                }
                for order in recent_orders
            ]
        }
    
    def validate_order_workflow(self, order_id: int, target_status: OrderStatus) -> bool:
        """Validate if order status transition is allowed.
        
        Args:
            order_id: Order ID
            target_status: Target status to transition to
            
        Returns:
            True if transition is valid, False otherwise
        """
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return False
        
        current_status = order.status
        
        # Define valid transitions
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.PAID, OrderStatus.CANCELED],
            OrderStatus.PAID: [OrderStatus.SHIPPED, OrderStatus.CANCELED],
            OrderStatus.SHIPPED: [],  # Final state
            OrderStatus.CANCELED: []  # Final state
        }
        
        return target_status in valid_transitions.get(current_status, [])

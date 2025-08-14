"""Order repository for data access operations."""

from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select

from ..models import Order, OrderStatus
from .base_repository import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Repository for Order operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Order)
    
    def get_by_status(self, status: OrderStatus) -> List[Order]:
        """Get orders by status."""
        statement = select(Order).where(Order.status == status)
        return list(self.session.exec(statement).all())
    
    def get_by_product_id(self, product_id: int) -> List[Order]:
        """Get orders for a specific product."""
        statement = select(Order).where(Order.product_id == product_id)
        return list(self.session.exec(statement).all())
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Order]:
        """Get orders within date range."""
        statement = select(Order).where(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )
        return list(self.session.exec(statement).all())
    
    def update_status(self, order_id: int, new_status: OrderStatus) -> Optional[Order]:
        """Update order status."""
        order = self.session.get(Order, order_id)
        if order:
            order.status = new_status
            self.session.add(order)
            self.session.commit()
            self.session.refresh(order)
            return order
        return None
    
    def get_pending_orders(self) -> List[Order]:
        """Get all pending orders."""
        return self.get_by_status(OrderStatus.PENDING)
    
    def get_recent_orders(self, limit: int = 10) -> List[Order]:
        """Get recent orders (most recent first)."""
        statement = select(Order).order_by(Order.created_at.desc()).limit(limit)
        return list(self.session.exec(statement).all())
    
    def get_orders_by_quantity_range(self, min_qty: int, max_qty: int) -> List[Order]:
        """Get orders within quantity range."""
        statement = select(Order).where(
            Order.quantity >= min_qty,
            Order.quantity <= max_qty
        )
        return list(self.session.exec(statement).all())

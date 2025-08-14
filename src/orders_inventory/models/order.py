"""Order model definition."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field, Index
from sqlalchemy import CheckConstraint, Column, DateTime
from pydantic import field_validator


class OrderStatus(str, Enum):
    """Allowed order statuses."""
    PENDING = "PENDING"
    PAID = "PAID" 
    SHIPPED = "SHIPPED"
    CANCELED = "CANCELED"


class Order(SQLModel, table=True):
    """Order model with status validation."""
    
    __tablename__ = "orders"
    
    # Fields
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    quantity: int = Field(gt=0)
    status: OrderStatus = Field(default=OrderStatus.PENDING, index=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False)
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        Index('idx_order_product_status', 'product_id', 'status'),
        Index('idx_order_created_at', 'created_at'),
        Index('idx_order_status', 'status'),
    )
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> OrderStatus:
        """Validate status is allowed."""
        if isinstance(v, str):
            try:
                return OrderStatus(v.upper())
            except ValueError:
                allowed_statuses = [status.value for status in OrderStatus]
                raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v

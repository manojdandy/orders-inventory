"""Product model definition."""

from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field, Index
from sqlalchemy import UniqueConstraint, CheckConstraint
from pydantic import field_validator


class Product(SQLModel, table=True):
    """Product model with constraints and validation."""
    
    __tablename__ = "products"
    
    # Fields
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(max_length=50, unique=True, index=True)
    name: str = Field(max_length=200)
    price: Decimal = Field(decimal_places=2, max_digits=10)
    stock: int = Field(ge=0, default=0)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('price > 0', name='check_price_positive'),
        CheckConstraint('stock >= 0', name='check_stock_non_negative'),
        UniqueConstraint('sku', name='uq_product_sku'),
        Index('idx_product_name', 'name'),
        Index('idx_product_price', 'price'),
        Index('idx_product_stock', 'stock'),
    )
    
    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Validate SKU format."""
        if not v or len(v.strip()) == 0:
            raise ValueError('SKU cannot be empty')
        if len(v) > 50:
            raise ValueError('SKU cannot exceed 50 characters')
        return v.strip().upper()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate product name."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Product name cannot be empty')
        if len(v) > 200:
            raise ValueError('Product name cannot exceed 200 characters')
        return v.strip()
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price is positive."""
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v
    
    @field_validator('stock')
    @classmethod
    def validate_stock(cls, v: int) -> int:
        """Validate stock is non-negative."""
        if v < 0:
            raise ValueError('Stock cannot be negative')
        return v

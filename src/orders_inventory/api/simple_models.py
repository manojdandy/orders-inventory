"""
Simplified Pydantic models for Render deployment.
Using basic Pydantic v1 models to avoid pydantic-core Rust compilation.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)


class OrderBase(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class Order(OrderBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderCreate(OrderBase):
    pass


class HealthResponse(BaseModel):
    status: str
    api_version: str = "1.0.0"


class ProductsResponse(BaseModel):
    products: List[Product]
    total: int
    page: int
    per_page: int
    pages: int

"""Pydantic models for API requests and responses."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from ..models import OrderStatus


# Base models
class BaseResponse(BaseModel):
    """Base response model with common fields."""
    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    """Error detail model."""
    type: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Product models
class ProductCreate(BaseModel):
    """Product creation request model."""
    sku: str = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="Unique product identifier (auto-converted to uppercase)",
        examples=["WIDGET-001", "GADGET-XL", "TOOL-SET-A"]
    )
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=200, 
        description="Human-readable product name",
        examples=["Premium Widget", "Extra Large Gadget", "Professional Tool Set"]
    )
    price: Decimal = Field(
        ..., 
        gt=0, 
        decimal_places=2, 
        description="Product price in currency units (max 2 decimal places)",
        examples=[19.99, 299.00, 1499.95]
    )
    stock: int = Field(
        ..., 
        ge=0, 
        description="Initial stock quantity (must be non-negative)",
        examples=[100, 50, 0]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "sku": "WIDGET-PRO-001",
                    "name": "Professional Widget Pro",
                    "price": 49.99,
                    "stock": 150
                },
                {
                    "sku": "GADGET-LITE",
                    "name": "Lightweight Gadget",
                    "price": 12.50,
                    "stock": 75
                },
                {
                    "sku": "TOOL-PREMIUM",
                    "name": "Premium Tool Set",
                    "price": 299.99,
                    "stock": 25
                }
            ]
        }
    )


class ProductUpdate(BaseModel):
    """Product update request model (partial updates allowed)."""
    sku: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=50, 
        description="Product SKU (must be unique if changed)",
        examples=["WIDGET-002", "UPDATED-SKU"]
    )
    name: Optional[str] = Field(
        None, 
        min_length=2, 
        max_length=200, 
        description="Product name",
        examples=["Updated Product Name", "New Description"]
    )
    price: Optional[Decimal] = Field(
        None, 
        gt=0, 
        decimal_places=2, 
        description="New product price",
        examples=[29.99, 199.95]
    )
    stock: Optional[int] = Field(
        None, 
        ge=0, 
        description="New stock quantity",
        examples=[200, 0, 50]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Updated Premium Widget",
                    "price": 59.99
                },
                {
                    "stock": 200
                },
                {
                    "name": "Completely Renamed Product",
                    "price": 89.99,
                    "stock": 75
                }
            ]
        }
    )


class ProductResponse(BaseResponse):
    """Product response model."""
    id: int
    sku: str
    name: str
    price: Decimal
    stock: int


class ProductListResponse(BaseModel):
    """Product list response with pagination."""
    products: List[ProductResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# Order models
class OrderCreate(BaseModel):
    """Order creation request model."""
    product_id: int = Field(
        ..., 
        gt=0, 
        description="ID of the product to order (must exist in inventory)",
        examples=[1, 42, 123]
    )
    quantity: int = Field(
        ..., 
        gt=0, 
        description="Quantity to order (must not exceed available stock)",
        examples=[1, 5, 10, 25]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "product_id": 1,
                    "quantity": 5
                },
                {
                    "product_id": 42,
                    "quantity": 10
                },
                {
                    "product_id": 123,
                    "quantity": 1
                }
            ]
        }
    )


class OrderUpdate(BaseModel):
    """Order update request model."""
    quantity: Optional[int] = Field(None, gt=0, description="Order quantity")
    status: Optional[OrderStatus] = Field(None, description="Order status")


class OrderResponse(BaseResponse):
    """Order response model."""
    id: int
    product_id: int
    quantity: int
    status: OrderStatus
    created_at: datetime


class OrderDetailResponse(BaseResponse):
    """Detailed order response with product information."""
    id: int
    product_id: int
    quantity: int
    status: OrderStatus
    created_at: datetime
    product: Optional[ProductResponse] = None
    total_value: Optional[Decimal] = None


class OrderListResponse(BaseModel):
    """Order list response with pagination."""
    orders: List[OrderResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# Status change models
class OrderStatusUpdate(BaseModel):
    """Order status update request."""
    status: OrderStatus = Field(..., description="New order status")


# Summary models
class InventorySummary(BaseModel):
    """Inventory summary response."""
    products: dict
    orders: dict


class OrdersSummary(BaseModel):
    """Orders summary response."""
    total_orders: int
    status_breakdown: dict
    total_quantity_ordered: int
    total_order_value: float
    recent_orders: List[dict]


# Search and filter models
class ProductFilters(BaseModel):
    """Product filtering parameters."""
    in_stock_only: Optional[bool] = False
    low_stock_threshold: Optional[int] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    search: Optional[str] = None


class OrderFilters(BaseModel):
    """Order filtering parameters."""
    status: Optional[OrderStatus] = None
    product_id: Optional[int] = None
    min_quantity: Optional[int] = None
    max_quantity: Optional[int] = None


# Pagination model
class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")


# Stock adjustment model
class StockAdjustment(BaseModel):
    """Stock adjustment request."""
    adjustment: int = Field(..., description="Stock adjustment (positive or negative)")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for adjustment")


# Success response models
class SuccessResponse(BaseModel):
    """Generic success response."""
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BulkOperationResponse(BaseModel):
    """Bulk operation response."""
    success_count: int
    failure_count: int
    failures: Optional[List[ErrorDetail]] = None

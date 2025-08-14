"""Product API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from .dependencies import get_inventory_service
from .models import (
    ProductCreate,
    ProductUpdate, 
    ProductResponse,
    ProductListResponse,
    SuccessResponse,
    StockAdjustment
)
from ..services import InventoryService
from ..utils.exceptions import DuplicateSKUError, ProductNotFoundError


router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="""
    **Create a new product in the inventory system.**
    
    This endpoint allows you to add new products to your catalog with automatic SKU validation, 
    price formatting, and initial stock allocation.
    
    ### Key Features:
    - **SKU Auto-formatting**: Automatically converts SKU to uppercase
    - **Unique Validation**: Ensures SKU uniqueness across the entire catalog
    - **Price Precision**: Validates price has maximum 2 decimal places
    - **Stock Management**: Sets initial stock level (can be zero for pre-orders)
    
    ### Business Rules:
    - SKU must be unique across all products (case-insensitive)
    - Price must be positive and have at most 2 decimal places
    - Stock quantity must be non-negative (zero allowed)
    - Product name must be at least 2 characters long
    
    ### Example Use Cases:
    - Adding new products to your catalog
    - Importing products from external systems
    - Creating placeholder products for future launches
    """,
    responses={
        201: {
            "description": "Product created successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "electronics": {
                            "summary": "Electronics Product",
                            "value": {
                                "id": 1,
                                "sku": "LAPTOP-PRO-001",
                                "name": "Professional Laptop Pro 15\"",
                                "price": 1299.99,
                                "stock": 25
                            }
                        },
                        "clothing": {
                            "summary": "Clothing Item",
                            "value": {
                                "id": 2,
                                "sku": "SHIRT-COTTON-M",
                                "name": "Premium Cotton Shirt - Medium",
                                "price": 49.99,
                                "stock": 100
                            }
                        }
                    }
                }
            }
        },
        409: {
            "description": "SKU already exists",
            "content": {
                "application/json": {
                    "example": {
                        "error": "DuplicateSKUError",
                        "details": [
                            {
                                "type": "DuplicateSKUError",
                                "message": "Product with SKU 'LAPTOP-PRO-001' already exists",
                                "field": "sku"
                            }
                        ],
                        "timestamp": "2023-01-01T12:00:00"
                    }
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ValidationError",
                        "details": [
                            {
                                "type": "ValidationError",
                                "message": "Price must be greater than 0",
                                "field": "price"
                            }
                        ],
                        "timestamp": "2023-01-01T12:00:00"
                    }
                }
            }
        }
    }
)
async def create_product(
    product_data: ProductCreate,
    inventory_service: InventoryService = Depends(get_inventory_service)
) -> ProductResponse:
    """
    Create a new product.
    
    **HTTP Status Codes:**
    - 201: Product created successfully
    - 409: Duplicate SKU conflict
    - 422: Validation error (invalid data)
    """
    try:
        product = inventory_service.add_product(
            sku=product_data.sku,
            name=product_data.name,
            price=float(product_data.price),
            stock=product_data.stock
        )
        return ProductResponse.model_validate(product)
    except DuplicateSKUError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="List products with pagination",
    description="Get paginated list of products with optional filters. Pagination is implemented to handle large inventories efficiently."
)
async def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    in_stock_only: bool = Query(False, description="Show only products in stock"),
    low_stock_threshold: Optional[int] = Query(None, ge=0, description="Show products below this stock level"),
    search: Optional[str] = Query(None, min_length=1, description="Search product names"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    inventory_service: InventoryService = Depends(get_inventory_service)
) -> ProductListResponse:
    """
    List products with pagination and filtering.
    
    **Pagination is implemented because:**
    - Large inventories can have thousands of products
    - Improves API performance and response times
    - Reduces memory usage on client side
    - Better user experience with progressive loading
    
    **HTTP Status Codes:**
    - 200: Success
    - 422: Invalid pagination parameters
    """
    # Get filtered products
    if low_stock_threshold is not None:
        products = inventory_service.list_products(low_stock_threshold=low_stock_threshold)
    elif in_stock_only:
        products = inventory_service.list_products(in_stock_only=True)
    else:
        products = inventory_service.list_products()
    
    # Apply search filter
    if search:
        products = inventory_service.search_products(search)
    
    # Apply price filters
    if min_price is not None or max_price is not None:
        filtered_products = []
        for product in products:
            price = float(product.price)
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            filtered_products.append(product)
        products = filtered_products
    
    # Calculate pagination
    total = len(products)
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_products = products[start_idx:end_idx]
    
    return ProductListResponse(
        products=[ProductResponse.model_validate(p) for p in paginated_products],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    description="Get a specific product by ID. Returns 404 if not found."
)
async def get_product(
    product_id: int,
    inventory_service: InventoryService = Depends(get_inventory_service)
) -> ProductResponse:
    """
    Get a product by ID.
    
    **Not-found response structure:**
    ```json
    {
        "error": "ProductNotFoundError",
        "details": [{
            "type": "ProductNotFoundError",
            "message": "Product with ID {id} not found",
            "field": null
        }],
        "timestamp": "2023-01-01T12:00:00"
    }
    ```
    
    **HTTP Status Codes:**
    - 200: Product found
    - 404: Product not found
    """
    product = inventory_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )
    return ProductResponse.model_validate(product)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product (partial updates allowed)",
    description="""
    **Update an existing product with flexible partial updates.**
    
    This endpoint supports partial updates using the HTTP PUT method with `exclude_unset=True`, 
    allowing you to update only the fields you specify while leaving others unchanged.
    
    ### Update Capabilities:
    - **Partial Updates**: Update any combination of fields
    - **Field Validation**: Each field is validated independently
    - **Business Rules**: Maintains all product constraints
    - **Atomic Operations**: All changes applied together or none at all
    
    ### Updatable Fields:
    - **SKU**: Must remain unique if changed
    - **Name**: Product display name (2-200 characters)
    - **Price**: Must be positive with max 2 decimal places  
    - **Stock**: Must be non-negative integer
    
    ### Common Update Scenarios:
    - **Price Changes**: Regular price updates for promotions/market changes
    - **Stock Adjustments**: Manual inventory corrections
    - **Product Information**: Name changes, rebranding
    - **SKU Modifications**: Rare but supported for product reorganization
    
    ### Important Notes:
    - Only provided fields are updated (partial update semantics)
    - Validation occurs on all provided fields
    - SKU uniqueness is enforced across entire catalog
    - Changes are applied atomically (all or nothing)
    """,
    responses={
        200: {
            "description": "Product updated successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "price_update": {
                            "summary": "Price Update Only",
                            "value": {
                                "id": 1,
                                "sku": "LAPTOP-PRO-001",
                                "name": "Professional Laptop Pro 15\"",
                                "price": 1199.99,  # Updated price
                                "stock": 25
                            }
                        },
                        "stock_adjustment": {
                            "summary": "Stock Adjustment Only",
                            "value": {
                                "id": 1,
                                "sku": "LAPTOP-PRO-001", 
                                "name": "Professional Laptop Pro 15\"",
                                "price": 1299.99,
                                "stock": 50  # Updated stock
                            }
                        },
                        "full_update": {
                            "summary": "Multiple Fields Updated",
                            "value": {
                                "id": 1,
                                "sku": "LAPTOP-PRO-002",  # Updated SKU
                                "name": "Professional Laptop Pro 15\" v2",  # Updated name
                                "price": 1399.99,  # Updated price
                                "stock": 30  # Updated stock
                            }
                        }
                    }
                }
            }
        }
    }
)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    inventory_service: InventoryService = Depends(get_inventory_service)
) -> ProductResponse:
    """
    Update a product (partial updates allowed).
    
    **Update Policy:**
    - Partial updates are allowed using exclude_unset=True
    - Only provided fields will be updated
    - Validation errors reject invalid fields
    - SKU uniqueness is enforced
    
    **Field Validation:**
    - SKU: 1-50 characters, alphanumeric + hyphens/underscores
    - Name: 2-200 characters
    - Price: Must be positive, max 2 decimal places
    - Stock: Must be non-negative integer
    
    **HTTP Status Codes:**
    - 200: Product updated successfully
    - 404: Product not found
    - 409: SKU conflict (if updating SKU to existing value)
    - 422: Validation error
    """
    # Check if product exists
    product = inventory_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Get only the fields that were provided (exclude unset)
    update_data = product_data.model_dump(exclude_unset=True)
    
    if not update_data:
        # No fields to update
        return ProductResponse.model_validate(product)
    
    try:
        updated_product = inventory_service.update_product(product_id, **update_data)
        if not updated_product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID {product_id} not found"
            )
        return ProductResponse.model_validate(updated_product)
    except DuplicateSKUError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=409, detail="SKU already exists")
        raise HTTPException(status_code=422, detail="Database constraint violation")


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
    description="Delete a product. Returns 204 No Content on success, 404 if not found."
)
async def delete_product(
    product_id: int,
    inventory_service: InventoryService = Depends(get_inventory_service)
):
    """
    Delete a product.
    
    **Success Status Code: 204 No Content**
    - RFC 7231 compliant
    - Indicates successful deletion
    - No response body needed
    - Idempotent operation
    
    **HTTP Status Codes:**
    - 204: Product deleted successfully
    - 404: Product not found
    """
    product = inventory_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Note: In a real system, you might want to check for existing orders
    # before allowing deletion, or implement soft deletion
    success = inventory_service.product_repo.delete(product_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )


@router.post(
    "/{product_id}/stock/adjust",
    response_model=ProductResponse,
    summary="Adjust product stock",
    description="Adjust product stock by a positive or negative amount."
)
async def adjust_stock(
    product_id: int,
    adjustment: StockAdjustment,
    inventory_service: InventoryService = Depends(get_inventory_service)
) -> ProductResponse:
    """
    Adjust product stock.
    
    **HTTP Status Codes:**
    - 200: Stock adjusted successfully
    - 404: Product not found
    - 422: Invalid adjustment (would result in negative stock)
    """
    product = inventory_service.adjust_stock(product_id, adjustment.adjustment)
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )
    return ProductResponse.model_validate(product)


@router.get(
    "/sku/{sku}",
    response_model=ProductResponse,
    summary="Get product by SKU",
    description="Get a specific product by SKU."
)
async def get_product_by_sku(
    sku: str,
    inventory_service: InventoryService = Depends(get_inventory_service)
) -> ProductResponse:
    """Get a product by SKU."""
    product = inventory_service.get_product_by_sku(sku)
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with SKU '{sku}' not found"
        )
    return ProductResponse.model_validate(product)

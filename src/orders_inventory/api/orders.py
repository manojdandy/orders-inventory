"""Order API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from .dependencies import get_inventory_service, get_order_service
from .models import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderDetailResponse,
    OrderListResponse,
    OrderStatusUpdate,
    SuccessResponse
)
from ..services import InventoryService, OrderService
from ..models import OrderStatus
from ..utils.exceptions import (
    ProductNotFoundError,
    OrderNotFoundError,
    InsufficientStockError,
    InvalidOrderStatusError
)


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="""
    **Create a new order with atomic stock management.**
    
    This is one of the most critical endpoints in the system, handling order creation with 
    guaranteed atomic stock reduction to prevent overselling and race conditions.
    
    ### Atomic Stock Management:
    - **Transaction Safety**: Stock check and reduction happen in a single database transaction
    - **Race Condition Prevention**: Concurrent orders cannot oversell inventory
    - **Rollback on Failure**: If any part fails, no changes are made to inventory
    - **Immediate Reservation**: Stock is reserved as soon as order is created (PENDING state)
    
    ### Business Logic:
    - Order starts in PENDING status automatically
    - Stock is immediately reduced by the ordered quantity  
    - Product must exist and have sufficient stock
    - Creates audit trail with timestamps
    
    ### Error Handling:
    - **409 Conflict**: Insufficient stock (includes available vs requested details)
    - **404 Not Found**: Product doesn't exist
    - **422 Validation**: Invalid quantity or product ID
    
    ### Typical Workflow:
    1. Customer places order → **POST /orders/** 
    2. Payment processing → **POST /orders/{id}/pay**
    3. Fulfillment → **POST /orders/{id}/ship**
    
    This endpoint is the entry point for all order processing and inventory management.
    """,
    responses={
        201: {
            "description": "Order created successfully, stock reduced",
            "content": {
                "application/json": {
                    "examples": {
                        "standard_order": {
                            "summary": "Standard Order Creation",
                            "value": {
                                "id": 1,
                                "product_id": 42,
                                "quantity": 5,
                                "status": "PENDING",
                                "created_at": "2023-01-01T12:00:00"
                            }
                        },
                        "bulk_order": {
                            "summary": "Large Quantity Order",
                            "value": {
                                "id": 2,
                                "product_id": 15,
                                "quantity": 100,
                                "status": "PENDING", 
                                "created_at": "2023-01-01T12:05:00"
                            }
                        }
                    }
                }
            }
        },
        409: {
            "description": "Insufficient stock conflict",
            "content": {
                "application/json": {
                    "example": {
                        "error": "InsufficientStockError",
                        "details": [
                            {
                                "type": "InsufficientStockError",
                                "message": "Insufficient stock. Available: 3, Requested: 5",
                                "field": "quantity"
                            }
                        ],
                        "timestamp": "2023-01-01T12:00:00"
                    }
                }
            }
        },
        404: {
            "description": "Product not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ProductNotFoundError",
                        "details": [
                            {
                                "type": "ProductNotFoundError",
                                "message": "Product with ID 999 not found",
                                "field": "product_id"
                            }
                        ],
                        "timestamp": "2023-01-01T12:00:00"
                    }
                }
            }
        }
    }
)
async def create_order(
    order_data: OrderCreate,
    inventory_service: InventoryService = Depends(get_inventory_service)
) -> OrderResponse:
    """
    Create a new order with atomic stock reduction.
    
    **Atomic Stock Handling:**
    - Stock is checked and reduced in a single database transaction
    - If insufficient stock, the entire operation is rolled back
    - No partial updates or race conditions
    - Stock reservation happens immediately upon order creation
    
    **Insufficient Stock Handling:**
    - Returns 409 Conflict with detailed error message
    - Includes available stock and requested quantity
    - No stock is modified if insufficient
    
    **HTTP Status Codes:**
    - 201: Order created successfully, stock reduced
    - 404: Product not found
    - 409: Insufficient stock conflict
    - 422: Invalid order data
    """
    try:
        order = inventory_service.create_order(
            product_id=order_data.product_id,
            quantity=order_data.quantity
        )
        return OrderResponse.model_validate(order)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientStockError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get(
    "/",
    response_model=OrderListResponse,
    summary="List orders with pagination and filters",
    description="Get paginated list of orders with optional status and product filters."
)
async def list_orders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    product_id: Optional[int] = Query(None, ge=1, description="Filter by product ID"),
    order_service: OrderService = Depends(get_order_service)
) -> OrderListResponse:
    """
    List orders with pagination and filtering.
    
    **HTTP Status Codes:**
    - 200: Success
    - 422: Invalid pagination parameters
    """
    # Get filtered orders
    orders = order_service.list_orders(status=status, product_id=product_id)
    
    # Calculate pagination
    total = len(orders)
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_orders = orders[start_idx:end_idx]
    
    return OrderListResponse(
        orders=[OrderResponse.model_validate(o) for o in paginated_orders],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get(
    "/{order_id}",
    response_model=OrderDetailResponse,
    summary="Get order details",
    description="Get detailed order information including product details and total value for tracking."
)
async def get_order(
    order_id: int,
    order_service: OrderService = Depends(get_order_service)
) -> OrderDetailResponse:
    """
    Get order details with comprehensive tracking data.
    
    **Basic Tracking Data Returned:**
    - Order ID, product ID, quantity, status, creation timestamp
    - Product details (SKU, name, price, current stock)
    - Total order value (price × quantity)
    - Order status for workflow tracking
    - Creation timestamp for time-based queries
    
    **HTTP Status Codes:**
    - 200: Order found
    - 404: Order not found
    """
    details = order_service.get_order_details(order_id)
    if not details:
        raise HTTPException(
            status_code=404,
            detail=f"Order with ID {order_id} not found"
        )
    
    return OrderDetailResponse(**details)


@router.put(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Update order (limited fields)",
    description="Update order with business rule validation. Only quantity and status can be changed with restrictions."
)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    inventory_service: InventoryService = Depends(get_inventory_service),
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """
    Update order with business rule enforcement.
    
    **Fields That Can Change:**
    - Quantity: Only for PENDING orders, subject to stock availability
    - Status: Following valid workflow transitions only
    
    **Invalid State Transition Handling:**
    - Validates against predefined workflow rules
    - PENDING → PAID, CANCELED
    - PAID → SHIPPED, CANCELED
    - SHIPPED → (no transitions, final state)
    - CANCELED → (no transitions, final state)
    - Returns 422 for invalid transitions with clear error message
    
    **Quantity Change Rules:**
    - Only allowed for PENDING orders
    - Must check stock availability for increases
    - Stock is adjusted accordingly
    
    **HTTP Status Codes:**
    - 200: Order updated successfully
    - 404: Order not found
    - 409: Insufficient stock for quantity increase
    - 422: Invalid state transition or business rule violation
    """
    # Get current order
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail=f"Order with ID {order_id} not found"
        )
    
    update_data = order_data.model_dump(exclude_unset=True)
    
    if not update_data:
        return OrderResponse.model_validate(order)
    
    try:
        # Handle status update
        if "status" in update_data:
            new_status = update_data["status"]
            
            # Validate workflow transition
            if not order_service.validate_order_workflow(order_id, new_status):
                current_status = order.status.value
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid status transition from {current_status} to {new_status.value}"
                )
            
            # Apply status change using service methods
            if new_status == OrderStatus.PAID and order.status == OrderStatus.PENDING:
                order = order_service.mark_as_paid(order_id)
            elif new_status == OrderStatus.SHIPPED and order.status == OrderStatus.PAID:
                order = order_service.ship_order(order_id)
            elif new_status == OrderStatus.CANCELED:
                order = order_service.cancel_order(order_id)
            else:
                # Direct status update for other cases
                order = order_service.order_repo.update_status(order_id, new_status)
        
        # Handle quantity update
        if "quantity" in update_data:
            new_quantity = update_data["quantity"]
            
            # Only allow quantity changes for PENDING orders
            if order.status != OrderStatus.PENDING:
                raise HTTPException(
                    status_code=422,
                    detail=f"Cannot change quantity for {order.status.value} orders. Only PENDING orders can be modified."
                )
            
            # Calculate stock adjustment needed
            quantity_diff = new_quantity - order.quantity
            
            if quantity_diff > 0:
                # Increasing quantity - need more stock
                product = inventory_service.get_product_by_id(order.product_id)
                if not product:
                    raise HTTPException(status_code=404, detail="Product not found")
                
                if product.stock < quantity_diff:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Insufficient stock. Available: {product.stock}, Additional needed: {quantity_diff}"
                    )
                
                # Reduce stock
                inventory_service.adjust_stock(order.product_id, -quantity_diff)
            elif quantity_diff < 0:
                # Decreasing quantity - restore stock
                inventory_service.adjust_stock(order.product_id, -quantity_diff)
            
            # Update order quantity
            order.quantity = new_quantity
            order = order_service.order_repo.update(order)
        
        return OrderResponse.model_validate(order)
        
    except InvalidOrderStatusError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except InsufficientStockError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except (ProductNotFoundError, OrderNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete(
    "/{order_id}",
    response_model=SuccessResponse,
    summary="Delete or cancel order",
    description="Delete/cancel order based on status. Uses cancel semantics for business logic, delete for administrative cleanup."
)
async def delete_order(
    order_id: int,
    force: bool = Query(False, description="Force delete instead of cancel (admin only)"),
    order_service: OrderService = Depends(get_order_service)
) -> SuccessResponse:
    """
    Delete or cancel order based on business rules.
    
    **When Deletion is Allowed vs Cancel Semantics:**
    
    **Cancel Semantics (Default):**
    - PENDING orders: Cancel and restore stock
    - PAID orders: Cancel and restore stock  
    - SHIPPED orders: Cannot be canceled (business rule)
    - CANCELED orders: Already canceled (idempotent)
    
    **Delete Semantics (force=true):**
    - Administrative function for data cleanup
    - Removes order record completely
    - Should be restricted to admin users in production
    - Does not restore stock (assumes already handled)
    
    **Business Logic:**
    - Default behavior uses cancel semantics for data integrity
    - Preserves audit trail and business workflow
    - Stock restoration maintains inventory accuracy
    - Force delete for administrative/testing purposes only
    
    **HTTP Status Codes:**
    - 200: Order canceled/deleted successfully
    - 404: Order not found  
    - 422: Cannot cancel shipped order (without force)
    """
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail=f"Order with ID {order_id} not found"
        )
    
    try:
        if force:
            # Administrative deletion - remove record completely
            success = order_service.order_repo.delete(order_id)
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Order with ID {order_id} not found"
                )
            return SuccessResponse(message=f"Order {order_id} deleted successfully")
        else:
            # Business cancellation - use cancel semantics
            canceled_order = order_service.cancel_order(order_id)
            return SuccessResponse(message=f"Order {order_id} canceled successfully")
            
    except InvalidOrderStatusError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{order_id}/pay",
    response_model=OrderResponse,
    summary="Mark order as paid",
    description="Transition order from PENDING to PAID status."
)
async def pay_order(
    order_id: int,
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """Mark order as paid."""
    try:
        order = order_service.mark_as_paid(order_id)
        return OrderResponse.model_validate(order)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidOrderStatusError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/{order_id}/ship",
    response_model=OrderResponse,
    summary="Mark order as shipped",
    description="Transition order from PAID to SHIPPED status."
)
async def ship_order(
    order_id: int,
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """Mark order as shipped."""
    try:
        order = order_service.ship_order(order_id)
        return OrderResponse.model_validate(order)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidOrderStatusError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel order",
    description="Cancel order and restore stock if applicable."
)
async def cancel_order(
    order_id: int,
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """Cancel order and restore stock."""
    try:
        order = order_service.cancel_order(order_id)
        return OrderResponse.model_validate(order)
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidOrderStatusError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get(
    "/recent",
    response_model=List[OrderResponse],
    summary="Get recent orders",
    description="Get most recent orders for dashboard/monitoring."
)
async def get_recent_orders(
    limit: int = Query(10, ge=1, le=50, description="Number of recent orders"),
    order_service: OrderService = Depends(get_order_service)
) -> List[OrderResponse]:
    """Get recent orders."""
    orders = order_service.get_recent_orders(limit=limit)
    return [OrderResponse.model_validate(o) for o in orders]

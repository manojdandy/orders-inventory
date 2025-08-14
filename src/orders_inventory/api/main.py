"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .products import router as products_router
from .orders import router as orders_router
from .exceptions import orders_inventory_exception_handler, validation_exception_handler
from ..utils.exceptions import OrdersInventoryError
from ..utils.database import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_database()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Orders & Inventory Management API",
    description="""
    # 📦 Orders & Inventory Management System
    
    A comprehensive REST API for managing products and orders with real-time inventory tracking and automated business workflows.
    
    ## 🚀 Key Features
    
    * **Product Management**: Complete CRUD operations with SKU validation and stock tracking
    * **Order Processing**: Full order lifecycle from creation to shipping with atomic stock updates
    * **Inventory Control**: Real-time stock management with low-stock alerts and adjustment tracking
    * **Business Rules**: Enforced order workflows and inventory constraints
    * **Data Validation**: Comprehensive input validation with detailed error responses
    * **Pagination**: Efficient handling of large datasets with configurable page sizes
    
    ## 📋 API Standards
    
    ### HTTP Status Codes
    * **200** OK - Successful GET/PUT operations
    * **201** Created - Successful POST operations (resource creation)
    * **204** No Content - Successful DELETE operations
    * **404** Not Found - Resource doesn't exist
    * **409** Conflict - Business rule violations (duplicate SKU, insufficient stock)
    * **422** Unprocessable Entity - Validation errors with field-level details
    
    ### Error Response Format
    All errors return structured JSON with details:
    ```json
    {
        "error": "ErrorType",
        "details": [
            {
                "type": "ErrorType",
                "message": "Human readable error message",
                "field": "fieldName"
            }
        ],
        "timestamp": "2023-01-01T12:00:00"
    }
    ```
    
    ## 🔄 Order Workflow
    
    Orders follow a strict state machine to ensure business integrity:
    
    ```
    PENDING ──→ PAID ──→ SHIPPED
        │        │
        ↓        ↓
    CANCELED ← CANCELED
    ```
    
    **Workflow Rules:**
    - PENDING orders can be modified (quantity) or canceled
    - PAID orders can only be shipped or canceled  
    - SHIPPED orders are final (no further transitions)
    - CANCELED orders are final (cannot be reactivated)
    
    ## 📊 Business Logic
    
    ### Stock Management
    - **Atomic Operations**: Stock updates and order creation in single transactions
    - **Immediate Reservation**: Stock reduced when order is created (PENDING state)
    - **Automatic Restoration**: Stock restored when orders are canceled
    - **Validation**: Prevents negative stock and overselling
    
    ### Data Integrity
    - **SKU Uniqueness**: Enforced at database and application level
    - **Price Validation**: Positive prices with 2 decimal precision
    - **Quantity Constraints**: Positive integers only
    - **Referential Integrity**: Orders reference valid products
    
    ## 🔗 Quick Start
    
    1. **Create a Product**: `POST /products/`
    2. **Browse Inventory**: `GET /products/`
    3. **Place an Order**: `POST /orders/`
    4. **Process Payment**: `POST /orders/{id}/pay`
    5. **Ship Order**: `POST /orders/{id}/ship`
    
    ## 📚 Documentation Access
    
    - **Interactive API Docs**: `/docs` (Swagger UI) - Try endpoints directly
    - **Alternative Docs**: `/redoc` (ReDoc) - Clean, printable documentation
    - **Health Check**: `/health` - API status and database connectivity
    - **System Summary**: `/summary` - Real-time inventory and order statistics
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@orders-inventory.com",
        "url": "https://github.com/your-org/orders-inventory"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    terms_of_service="https://orders-inventory.com/terms",
    openapi_tags=[
        {
            "name": "products",
            "description": "**Product Management Operations**\n\nManage your product catalog with full CRUD capabilities. Includes inventory tracking, SKU validation, and stock management features."
        },
        {
            "name": "orders", 
            "description": "**Order Processing & Lifecycle**\n\nComplete order management from creation to fulfillment. Handles payment processing, shipping, cancellations, and automatic inventory updates."
        },
        {
            "name": "health",
            "description": "**System Health & Monitoring**\n\nAPI health checks and system status endpoints for monitoring and diagnostics."
        },
        {
            "name": "reporting",
            "description": "**Analytics & Reporting**\n\nBusiness intelligence endpoints providing inventory summaries, order analytics, and operational insights."
        }
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(OrdersInventoryError, orders_inventory_exception_handler)
app.add_exception_handler(Exception, validation_exception_handler)

# Include routers
app.include_router(products_router)
app.include_router(orders_router)


@app.get("/", tags=["health"])
async def root():
    """Health check endpoint."""
    return {
        "message": "Orders & Inventory Management API",
        "status": "healthy",
        "docs": "/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Detailed health check."""
    from ..utils.database import get_database_info
    
    try:
        db_info = get_database_info()
        return {
            "status": "healthy",
            "database": {
                "connected": True,
                "type": "sqlite" if db_info["is_sqlite"] else "other",
                "url": db_info["database_url"]
            },
            "api_version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": {
                "connected": False,
                "error": str(e)
            },
            "api_version": "1.0.0"
        }


@app.get("/summary", tags=["reporting"])
async def get_summary():
    """Get overall system summary."""
    from .dependencies import get_inventory_service, get_order_service
    from ..utils.database import get_db_session
    
    session = get_db_session()
    try:
        inventory_service = get_inventory_service(session)
        order_service = get_order_service(session)
        
        inventory_summary = inventory_service.get_inventory_summary()
        orders_summary = order_service.get_orders_summary()
        
        return {
            "inventory": inventory_summary,
            "orders": orders_summary
        }
    finally:
        session.close()

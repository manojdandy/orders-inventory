"""
Simplified FastAPI app for Render deployment.
Avoids SQLModel and pydantic-core Rust compilation issues.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import os
from datetime import datetime

# Simple in-memory storage for demo
products_db: Dict[int, Dict[str, Any]] = {}
orders_db: Dict[int, Dict[str, Any]] = {}
next_product_id = 1
next_order_id = 1

app = FastAPI(
    title="Orders & Inventory Management API",
    description="Simplified API for Render deployment",
    version="1.0.0"
)

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Orders & Inventory Management API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": {
            "connected": True,
            "type": "in-memory",
            "products_count": len(products_db),
            "orders_count": len(orders_db)
        },
        "api_version": "1.0.0"
    }


@app.get("/products/")
async def list_products(page: int = 1, per_page: int = 20):
    """List all products with pagination."""
    start = (page - 1) * per_page
    end = start + per_page
    
    products_list = list(products_db.values())
    paginated_products = products_list[start:end]
    
    return {
        "products": paginated_products,
        "total": len(products_list),
        "page": page,
        "per_page": per_page,
        "pages": (len(products_list) + per_page - 1) // per_page
    }


@app.post("/products/", status_code=201)
async def create_product(product_data: dict):
    """Create a new product."""
    global next_product_id
    
    # Basic validation
    required_fields = ["sku", "name", "price", "stock"]
    for field in required_fields:
        if field not in product_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    # Check for duplicate SKU
    for product in products_db.values():
        if product["sku"] == product_data["sku"]:
            raise HTTPException(status_code=409, detail="SKU already exists")
    
    # Validate data types
    try:
        price = float(product_data["price"])
        stock = int(product_data["stock"])
        if price <= 0:
            raise HTTPException(status_code=422, detail="Price must be greater than 0")
        if stock < 0:
            raise HTTPException(status_code=422, detail="Stock must be non-negative")
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid price or stock value")
    
    product = {
        "id": next_product_id,
        "sku": product_data["sku"].upper(),
        "name": product_data["name"],
        "price": price,
        "stock": stock,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    products_db[next_product_id] = product
    next_product_id += 1
    
    return product


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """Get a specific product."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return products_db[product_id]


@app.put("/products/{product_id}")
async def update_product(product_id: int, update_data: dict):
    """Update a product."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[product_id].copy()
    
    # Update allowed fields
    allowed_fields = ["name", "price", "stock"]
    for field in allowed_fields:
        if field in update_data:
            if field == "price":
                try:
                    value = float(update_data[field])
                    if value <= 0:
                        raise HTTPException(status_code=422, detail="Price must be greater than 0")
                    product[field] = value
                except (ValueError, TypeError):
                    raise HTTPException(status_code=422, detail="Invalid price value")
            elif field == "stock":
                try:
                    value = int(update_data[field])
                    if value < 0:
                        raise HTTPException(status_code=422, detail="Stock must be non-negative")
                    product[field] = value
                except (ValueError, TypeError):
                    raise HTTPException(status_code=422, detail="Invalid stock value")
            else:
                product[field] = update_data[field]
    
    product["updated_at"] = datetime.utcnow().isoformat()
    products_db[product_id] = product
    
    return product


@app.post("/orders/", status_code=201)
async def create_order(order_data: dict):
    """Create a new order."""
    global next_order_id
    
    # Basic validation
    required_fields = ["product_id", "quantity"]
    for field in required_fields:
        if field not in order_data:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")
    
    try:
        product_id = int(order_data["product_id"])
        quantity = int(order_data["quantity"])
        if quantity <= 0:
            raise HTTPException(status_code=422, detail="Quantity must be greater than 0")
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid product_id or quantity")
    
    # Check if product exists
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[product_id]
    
    # Check stock availability
    if product["stock"] < quantity:
        raise HTTPException(status_code=409, detail="Insufficient stock")
    
    # Create order and update stock
    order = {
        "id": next_order_id,
        "product_id": product_id,
        "quantity": quantity,
        "status": "PENDING",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Update product stock
    product["stock"] -= quantity
    product["updated_at"] = datetime.utcnow().isoformat()
    products_db[product_id] = product
    
    orders_db[next_order_id] = order
    next_order_id += 1
    
    return order


@app.get("/orders/")
async def list_orders(page: int = 1, per_page: int = 20):
    """List all orders with pagination."""
    start = (page - 1) * per_page
    end = start + per_page
    
    orders_list = list(orders_db.values())
    paginated_orders = orders_list[start:end]
    
    return {
        "orders": paginated_orders,
        "total": len(orders_list),
        "page": page,
        "per_page": per_page,
        "pages": (len(orders_list) + per_page - 1) // per_page
    }


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    """Get a specific order."""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return orders_db[order_id]


@app.get("/summary")
async def get_summary():
    """Get system summary."""
    total_value = sum(p["price"] * p["stock"] for p in products_db.values())
    
    return {
        "inventory": {
            "total_products": len(products_db),
            "total_stock": sum(p["stock"] for p in products_db.values()),
            "total_value": total_value,
            "low_stock_products": sum(1 for p in products_db.values() if p["stock"] < 10)
        },
        "orders": {
            "total_orders": len(orders_db),
            "pending_orders": sum(1 for o in orders_db.values() if o["status"] == "PENDING"),
            "total_quantity": sum(o["quantity"] for o in orders_db.values())
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

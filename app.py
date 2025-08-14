"""
Simple FastAPI app - no external dependencies beyond FastAPI and Uvicorn.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import os
from datetime import datetime

# Simple in-memory storage
products_db: Dict[int, Dict[str, Any]] = {}
orders_db: Dict[int, Dict[str, Any]] = {}
next_product_id = 1
next_order_id = 1

app = FastAPI(
    title="Orders & Inventory Management API",
    description="Simple API for Render deployment",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    port = os.getenv("PORT", "not set")
    return {
        "message": "Orders & Inventory Management API", 
        "version": "1.0.0",
        "port": port,
        "host": "0.0.0.0"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": {"connected": True, "type": "in-memory"},
        "api_version": "1.0.0"
    }

@app.get("/products/")
def list_products():
    return {"products": list(products_db.values()), "total": len(products_db)}

@app.post("/products/", status_code=201)
def create_product(product: dict):
    global next_product_id
    
    # Basic validation
    if "sku" not in product or "name" not in product or "price" not in product or "stock" not in product:
        raise HTTPException(status_code=422, detail="Missing required fields")
    
    # Check duplicate SKU
    for p in products_db.values():
        if p["sku"] == product["sku"]:
            raise HTTPException(status_code=409, detail="SKU already exists")
    
    new_product = {
        "id": next_product_id,
        "sku": str(product["sku"]).upper(),
        "name": str(product["name"]),
        "price": float(product["price"]),
        "stock": int(product["stock"]),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    products_db[next_product_id] = new_product
    next_product_id += 1
    
    return new_product

@app.get("/products/{product_id}")
def get_product(product_id: int):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]

@app.post("/orders/", status_code=201)
def create_order(order: dict):
    global next_order_id
    
    if "product_id" not in order or "quantity" not in order:
        raise HTTPException(status_code=422, detail="Missing required fields")
    
    product_id = int(order["product_id"])
    quantity = int(order["quantity"])
    
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[product_id]
    if product["stock"] < quantity:
        raise HTTPException(status_code=409, detail="Insufficient stock")
    
    # Create order and update stock
    new_order = {
        "id": next_order_id,
        "product_id": product_id,
        "quantity": quantity,
        "status": "PENDING",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    product["stock"] -= quantity
    orders_db[next_order_id] = new_order
    next_order_id += 1
    
    return new_order

@app.get("/orders/")
def list_orders():
    return {"orders": list(orders_db.values()), "total": len(orders_db)}

@app.get("/summary")
def summary():
    return {
        "inventory": {"total_products": len(products_db)},
        "orders": {"total_orders": len(orders_db)}
    }

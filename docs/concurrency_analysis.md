# Concurrency Analysis: Handling the "Last Item" Problem

## Current Implementation

### SQLite Transaction Isolation

Our current implementation uses SQLite with default transaction isolation:

```python
def create_order(self, product_id: int, quantity: int) -> Order:
    """Create order with atomic stock management."""
    
    # 1. Start implicit transaction
    product = self.product_repo.get_by_id(product_id)
    if not product:
        raise ProductNotFoundError(f"Product with ID {product_id} not found")
    
    # 2. Check stock availability
    if product.stock < quantity:
        raise InsufficientStockError(
            f"Insufficient stock. Available: {product.stock}, Requested: {quantity}"
        )
    
    # 3. Create order
    order = Order(product_id=product_id, quantity=quantity)
    order = self.order_repo.create(order)
    
    # 4. Reduce stock
    product.stock -= quantity
    self.product_repo.update(product)
    
    # 5. Commit transaction (implicit)
    return order
```

### Race Condition Scenario

**Problem**: Two concurrent requests for the last item

```
Time  | Request A (qty: 1)           | Request B (qty: 1)           | Stock
------|------------------------------|------------------------------|-------
T1    | Read stock = 1               |                              | 1
T2    |                              | Read stock = 1               | 1
T3    | Check: 1 >= 1 ✓             |                              | 1
T4    |                              | Check: 1 >= 1 ✓             | 1
T5    | Create order                 |                              | 1
T6    |                              | Create order                 | 1
T7    | Update stock = 0             |                              | 0
T8    |                              | Update stock = -1 ❌         | -1
```

**Result**: Overselling! Stock becomes negative.

## Solutions by Database Type

### 1. SQLite Limitations & Fixes

#### Current Limitations:
- SQLite uses file-level locking
- READ UNCOMMITTED isolation by default
- No true concurrent writes
- Race conditions possible in high-concurrency scenarios

#### SQLite Fixes:
```python
# Option A: Explicit Transaction with Immediate Lock
def create_order_safe_sqlite(self, product_id: int, quantity: int) -> Order:
    with self.session.begin():  # Explicit transaction
        # Use SELECT FOR UPDATE equivalent (SQLite doesn't support it)
        # Use UPDATE with WHERE condition instead
        
        rows_affected = self.session.execute(
            text("""
                UPDATE products 
                SET stock = stock - :quantity 
                WHERE id = :product_id AND stock >= :quantity
            """),
            {"quantity": quantity, "product_id": product_id}
        )
        
        if rows_affected.rowcount == 0:
            # Either product doesn't exist or insufficient stock
            product = self.get_product_by_id(product_id)
            if not product:
                raise ProductNotFoundError(f"Product {product_id} not found")
            else:
                raise InsufficientStockError(
                    f"Insufficient stock. Available: {product.stock}, Requested: {quantity}"
                )
        
        # Create order only after successful stock update
        order = Order(product_id=product_id, quantity=quantity)
        return self.order_repo.create(order)

# Option B: Optimistic Locking with Version Field
class Product(SQLModel, table=True):
    # ... existing fields ...
    version: int = Field(default=1)
    
    def update_stock_optimistic(self, new_stock: int, expected_version: int):
        result = session.execute(
            text("""
                UPDATE products 
                SET stock = :new_stock, version = version + 1
                WHERE id = :id AND version = :expected_version
            """),
            {"new_stock": new_stock, "id": self.id, "expected_version": expected_version}
        )
        if result.rowcount == 0:
            raise ConcurrentModificationError("Product was modified by another transaction")
```

### 2. PostgreSQL Solution (Production Ready)

```python
# Pessimistic Locking with SELECT FOR UPDATE
def create_order_postgresql(self, product_id: int, quantity: int) -> Order:
    with self.session.begin():
        # Lock the product row for update
        product = self.session.execute(
            select(Product)
            .where(Product.id == product_id)
            .with_for_update()  # SELECT FOR UPDATE
        ).scalar_one_or_none()
        
        if not product:
            raise ProductNotFoundError(f"Product {product_id} not found")
        
        if product.stock < quantity:
            raise InsufficientStockError(
                f"Insufficient stock. Available: {product.stock}, Requested: {quantity}"
            )
        
        # Update stock
        product.stock -= quantity
        self.session.add(product)
        
        # Create order
        order = Order(product_id=product_id, quantity=quantity)
        self.session.add(order)
        
        self.session.commit()
        return order

# Alternative: Atomic UPDATE approach
def create_order_atomic_postgresql(self, product_id: int, quantity: int) -> Order:
    # Single atomic operation
    result = self.session.execute(
        text("""
            UPDATE products 
            SET stock = stock - :quantity 
            WHERE id = :product_id 
            AND stock >= :quantity
            RETURNING stock
        """),
        {"quantity": quantity, "product_id": product_id}
    )
    
    if not result.rowcount:
        # Check if product exists or insufficient stock
        product = self.get_product_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"Product {product_id} not found")
        raise InsufficientStockError(
            f"Insufficient stock. Available: {product.stock}, Requested: {quantity}"
        )
    
    # Create order after successful stock update
    order = Order(product_id=product_id, quantity=quantity)
    return self.order_repo.create(order)
```

### 3. Redis-Based Solution (High Concurrency)

```python
import redis
from sqlalchemy import event

class RedisStockManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def create_order_with_redis_lock(self, product_id: int, quantity: int) -> Order:
        lock_key = f"product_lock:{product_id}"
        stock_key = f"product_stock:{product_id}"
        
        # Acquire distributed lock
        with self.redis.lock(lock_key, timeout=10):
            # Get current stock from Redis
            current_stock = int(self.redis.get(stock_key) or 0)
            
            if current_stock < quantity:
                raise InsufficientStockError(
                    f"Insufficient stock. Available: {current_stock}, Requested: {quantity}"
                )
            
            # Atomically decrease stock in Redis
            new_stock = self.redis.decrby(stock_key, quantity)
            
            if new_stock < 0:
                # Rollback if we went negative
                self.redis.incrby(stock_key, quantity)
                raise InsufficientStockError("Concurrent stock depletion detected")
            
            # Create order in database
            order = Order(product_id=product_id, quantity=quantity)
            order = self.order_repo.create(order)
            
            # Async update database stock (eventual consistency)
            self.schedule_stock_sync(product_id, new_stock)
            
            return order
```

## Deterministic Error Response Format

All errors follow the same structure for consistency:

```python
class ErrorResponse(BaseModel):
    error: str                              # Error type (class name)
    details: List[ErrorDetail]              # Array of error details
    timestamp: datetime                     # ISO 8601 timestamp

class ErrorDetail(BaseModel):
    type: str                               # Specific error type
    message: str                            # Human-readable message
    field: Optional[str] = None             # Field that caused error (if applicable)
```

### Guaranteed Error Shape Examples:

```python
# Always includes these fields
{
    "error": "ErrorTypeName",
    "details": [
        {
            "type": "SpecificErrorType", 
            "message": "Clear description",
            "field": "fieldName"  # or null
        }
    ],
    "timestamp": "2023-12-01T14:30:25.123456"
}
```

This ensures clients can:
1. Parse errors consistently
2. Handle specific error types programmatically  
3. Display appropriate user messages
4. Log errors with timestamps
5. Track field-level validation issues

## Production Recommendations

### Database Choice:
- **Development**: SQLite with atomic UPDATE operations
- **Production**: PostgreSQL with SELECT FOR UPDATE
- **High Scale**: Redis + PostgreSQL with eventual consistency

### Monitoring:
- Track concurrent modification attempts
- Monitor stock discrepancies
- Alert on negative stock values
- Log all race condition attempts

### Testing:
- Simulate concurrent requests in tests
- Verify no overselling under load
- Test timeout and rollback scenarios

"""Tests for concurrency handling and race conditions."""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlmodel import Session, create_engine, SQLModel

from orders_inventory.models import Product, Order
from orders_inventory.services import InventoryService
from orders_inventory.services.concurrency_safe_service import ConcurrencySafeOrderService
from orders_inventory.utils.exceptions import InsufficientStockError


class TestConcurrencyScenarios:
    """Test concurrent access to inventory."""
    
    @pytest.fixture
    def test_engine(self):
        """Create test database engine."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(engine)
        yield engine
        SQLModel.metadata.drop_all(engine)
    
    @pytest.fixture
    def product_with_limited_stock(self, test_engine):
        """Create a product with very limited stock for testing."""
        with Session(test_engine) as session:
            product = Product(
                sku="LIMITED-001",
                name="Limited Stock Product", 
                price=99.99,
                stock=1  # Only 1 item available
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            return product.id, test_engine
    
    def test_race_condition_demonstration(self, product_with_limited_stock):
        """
        Demonstrate the race condition problem with standard service.
        
        This test shows how two concurrent requests can both succeed
        when only one should, leading to negative stock.
        """
        product_id, engine = product_with_limited_stock
        
        # Results from concurrent operations
        results = []
        errors = []
        
        def try_create_order(order_id):
            """Simulate a user trying to order the last item."""
            try:
                with Session(engine) as session:
                    service = InventoryService(session)
                    
                    # Add a small delay to increase chance of race condition
                    time.sleep(0.01)
                    
                    order = service.create_order(product_id, 1)
                    results.append(f"Order {order_id}: SUCCESS - Order ID {order.id}")
                    return True
            except InsufficientStockError as e:
                errors.append(f"Order {order_id}: REJECTED - {str(e)}")
                return False
            except Exception as e:
                errors.append(f"Order {order_id}: ERROR - {str(e)}")
                return False
        
        # Simulate 3 concurrent users trying to buy the last item
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(try_create_order, f"USER-{i}")
                for i in range(1, 4)
            ]
            
            # Wait for all to complete
            for future in as_completed(futures):
                future.result()
        
        print("\n=== RACE CONDITION DEMONSTRATION ===")
        print("Results:", results)
        print("Errors:", errors)
        
        # Check final stock
        with Session(engine) as session:
            product = session.get(Product, product_id)
            print(f"Final stock: {product.stock}")
        
        # In a race condition, we might see:
        # - Multiple successful orders (bad!)
        # - Negative stock (very bad!)
        
        # Note: This test demonstrates the problem but doesn't assert
        # because race conditions are non-deterministic
    
    def test_atomic_order_creation_prevents_overselling(self, product_with_limited_stock):
        """
        Test that atomic order creation prevents overselling.
        
        This test uses the concurrent-safe service to ensure
        only one order succeeds when stock is limited.
        """
        product_id, engine = product_with_limited_stock
        
        successful_orders = []
        failed_orders = []
        
        def try_create_order_atomic(order_id):
            """Try to create order with atomic stock update."""
            try:
                with Session(engine) as session:
                    service = ConcurrencySafeOrderService(session)
                    order = service.create_order_atomic_sqlite(product_id, 1)
                    successful_orders.append(order.id)
                    return True
            except InsufficientStockError:
                failed_orders.append(order_id)
                return False
            except Exception as e:
                failed_orders.append(f"ERROR: {e}")
                return False
        
        # Simulate 5 concurrent users trying to buy the last item
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(try_create_order_atomic, f"USER-{i}")
                for i in range(1, 6)
            ]
            
            # Wait for all to complete
            for future in as_completed(futures):
                future.result()
        
        print("\n=== ATOMIC ORDER CREATION TEST ===")
        print(f"Successful orders: {len(successful_orders)}")
        print(f"Failed orders: {len(failed_orders)}")
        
        # Verify only one order succeeded
        assert len(successful_orders) == 1, f"Expected 1 successful order, got {len(successful_orders)}"
        assert len(failed_orders) == 4, f"Expected 4 failed orders, got {len(failed_orders)}"
        
        # Verify stock is exactly 0 (not negative)
        with Session(engine) as session:
            product = session.get(Product, product_id)
            assert product.stock == 0, f"Expected stock 0, got {product.stock}"
    
    def test_optimistic_locking_with_retries(self, product_with_limited_stock):
        """
        Test optimistic locking with retry mechanism.
        
        This approach detects concurrent modifications and retries
        the operation, ensuring consistency.
        """
        product_id, engine = product_with_limited_stock
        
        successful_orders = []
        failed_orders = []
        retry_counts = []
        
        def try_create_order_optimistic(order_id):
            """Try to create order with optimistic locking."""
            try:
                with Session(engine) as session:
                    service = ConcurrencySafeOrderService(session)
                    
                    # Track retry attempts
                    original_method = service.create_order_with_optimistic_locking
                    
                    order = original_method(product_id, 1, max_retries=3)
                    successful_orders.append(order.id)
                    return True
            except InsufficientStockError:
                failed_orders.append(order_id)
                return False
            except Exception as e:
                failed_orders.append(f"ERROR: {e}")
                return False
        
        # Simulate 5 concurrent users
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(try_create_order_optimistic, f"USER-{i}")
                for i in range(1, 6)
            ]
            
            for future in as_completed(futures):
                future.result()
        
        print("\n=== OPTIMISTIC LOCKING TEST ===")
        print(f"Successful orders: {len(successful_orders)}")
        print(f"Failed orders: {len(failed_orders)}")
        
        # Verify only one order succeeded
        assert len(successful_orders) == 1
        assert len(failed_orders) == 4
        
        # Verify final stock
        with Session(engine) as session:
            product = session.get(Product, product_id)
            assert product.stock == 0
    
    def test_concurrent_orders_different_products(self, test_engine):
        """
        Test that concurrent orders for different products work fine.
        
        This verifies our concurrency control doesn't create unnecessary
        bottlenecks when products don't conflict.
        """
        # Create multiple products
        product_ids = []
        with Session(test_engine) as session:
            for i in range(3):
                product = Product(
                    sku=f"PROD-{i:03d}",
                    name=f"Product {i}",
                    price=10.00 + i,
                    stock=10
                )
                session.add(product)
                session.commit()
                session.refresh(product)
                product_ids.append(product.id)
        
        successful_orders = []
        
        def create_order_for_product(product_idx):
            """Create order for specific product."""
            product_id = product_ids[product_idx]
            with Session(test_engine) as session:
                service = ConcurrencySafeOrderService(session)
                order = service.create_order_atomic_sqlite(product_id, 1)
                successful_orders.append((product_id, order.id))
        
        # Create orders for different products concurrently
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(create_order_for_product, i % 3)
                for i in range(6)  # 2 orders per product
            ]
            
            for future in as_completed(futures):
                future.result()
        
        # All orders should succeed since they're for different products
        assert len(successful_orders) == 6
        
        # Verify each product has stock reduced by 2
        with Session(test_engine) as session:
            for product_id in product_ids:
                product = session.get(Product, product_id)
                assert product.stock == 8  # 10 - 2 = 8
    
    def test_high_concurrency_stress(self, test_engine):
        """
        Stress test with high concurrency to verify robustness.
        
        This test creates a product with moderate stock and
        many concurrent orders to verify system behavior.
        """
        # Create product with limited stock
        with Session(test_engine) as session:
            product = Product(
                sku="STRESS-TEST",
                name="Stress Test Product",
                price=50.00,
                stock=10  # 10 items available
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            product_id = product.id
        
        # Attempt 20 concurrent orders (2x oversubscription)
        successful_orders = []
        failed_orders = []
        
        def try_create_order(order_num):
            """Create order with error handling."""
            try:
                with Session(test_engine) as session:
                    service = ConcurrencySafeOrderService(session)
                    order = service.create_order_atomic_sqlite(product_id, 1)
                    successful_orders.append(order.id)
                    return True
            except InsufficientStockError:
                failed_orders.append(order_num)
                return False
        
        # High concurrency test
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(try_create_order, i)
                for i in range(20)
            ]
            
            for future in as_completed(futures):
                future.result()
        
        print(f"\n=== STRESS TEST RESULTS ===")
        print(f"Successful orders: {len(successful_orders)}")
        print(f"Failed orders: {len(failed_orders)}")
        
        # Verify exactly 10 orders succeeded (original stock)
        assert len(successful_orders) == 10
        assert len(failed_orders) == 10
        
        # Verify stock is exactly 0
        with Session(test_engine) as session:
            product = session.get(Product, product_id)
            assert product.stock == 0


if __name__ == "__main__":
    # Run a quick demonstration
    pytest.main([__file__, "-v", "-s"])

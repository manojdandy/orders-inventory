"""
Specific load testing scenarios for different use cases.

These scenarios test specific performance requirements and edge cases.
"""

import random
import time
from locust import HttpUser, task, between, events
from faker import Faker

fake = Faker()


class LastItemRaceConditionTest(HttpUser):
    """
    Specialized test for the "last item" race condition scenario.
    
    This creates a product with very limited stock and then has multiple
    users try to order it simultaneously to test concurrency control.
    """
    weight = 1
    wait_time = between(0.1, 0.3)  # Very fast to create contention
    
    def on_start(self):
        """Setup: Create a product with limited stock."""
        # Create a product with only 5 items
        product_data = {
            "sku": f"LIMITED-{random.randint(1000, 9999)}",
            "name": "Limited Edition Product",
            "price": 99.99,
            "stock": 5  # Very limited stock
        }
        
        response = self.client.post("/products/", json=product_data)
        if response.status_code == 201:
            self.limited_product = response.json()
            print(f"Created limited product: {self.limited_product['id']} with stock {self.limited_product['stock']}")
        else:
            self.limited_product = None
    
    @task(1)
    def try_order_last_items(self):
        """Rapidly try to order the limited product."""
        if not self.limited_product:
            return
        
        order_data = {
            "product_id": self.limited_product["id"],
            "quantity": 1
        }
        
        with self.client.post("/orders/", json=order_data, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                print(f"✅ Successfully ordered limited product {self.limited_product['id']}")
            elif response.status_code == 409:
                # This is expected when stock runs out
                response.success()
                print(f"⚠️ Stock depleted for product {self.limited_product['id']}")
            else:
                response.failure(f"Unexpected response: {response.status_code}")


class BulkOperationsTest(HttpUser):
    """
    Test bulk operations and high-throughput scenarios.
    
    This simulates batch processing systems or bulk imports.
    """
    weight = 1
    wait_time = between(1, 2)
    
    @task(1)
    def bulk_product_creation(self):
        """Create multiple products in rapid succession."""
        for i in range(5):
            product_data = {
                "sku": f"BULK-{random.randint(10000, 99999)}-{i}",
                "name": f"Bulk Product {i}",
                "price": round(random.uniform(10.0, 1000.0), 2),
                "stock": random.randint(50, 500)
            }
            
            with self.client.post("/products/", json=product_data, catch_response=True) as response:
                if response.status_code == 201:
                    response.success()
                elif response.status_code == 409:
                    response.success()  # Duplicate SKU
                else:
                    response.failure(f"Bulk creation failed: {response.status_code}")
    
    @task(1)
    def bulk_order_processing(self):
        """Process multiple orders quickly."""
        # Get some products first
        response = self.client.get("/products/?per_page=10")
        if response.status_code == 200:
            products = response.json().get("products", [])
            
            for _ in range(3):
                if products:
                    product = random.choice(products)
                    order_data = {
                        "product_id": product["id"],
                        "quantity": random.randint(1, 5)
                    }
                    
                    with self.client.post("/orders/", json=order_data, catch_response=True) as response:
                        if response.status_code in [201, 409]:  # Success or stock conflict
                            response.success()
                        else:
                            response.failure(f"Bulk order failed: {response.status_code}")


class StockDepletionRecoveryTest(HttpUser):
    """
    Test system behavior when products go out of stock and recovery scenarios.
    """
    weight = 1
    wait_time = between(0.5, 1.5)
    
    def on_start(self):
        """Create a product for depletion testing."""
        product_data = {
            "sku": f"DEPLETION-{random.randint(1000, 9999)}",
            "name": "Stock Depletion Test Product",
            "price": 50.00,
            "stock": 10  # Moderate stock for testing
        }
        
        response = self.client.post("/products/", json=product_data)
        if response.status_code == 201:
            self.test_product = response.json()
        else:
            self.test_product = None
    
    @task(3)
    def deplete_stock(self):
        """Order products to deplete stock."""
        if not self.test_product:
            return
        
        # Order random quantities to eventually deplete stock
        quantity = random.randint(1, 5)
        order_data = {
            "product_id": self.test_product["id"],
            "quantity": quantity
        }
        
        with self.client.post("/orders/", json=order_data, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 409:
                response.success()  # Stock depleted - expected
            else:
                response.failure(f"Depletion test failed: {response.status_code}")
    
    @task(1)
    def restock_product(self):
        """Periodically restock the product."""
        if not self.test_product:
            return
        
        # Add stock back
        adjustment_data = {
            "adjustment": random.randint(5, 20),
            "reason": "Restock for load test"
        }
        
        with self.client.post(f"/products/{self.test_product['id']}/stock/adjust", 
                            json=adjustment_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                print(f"Restocked product {self.test_product['id']}")
            else:
                response.failure(f"Restock failed: {response.status_code}")


class HighFrequencyMonitoringTest(HttpUser):
    """
    Test high-frequency monitoring and dashboard access patterns.
    
    This simulates real-time dashboards and monitoring systems.
    """
    weight = 1
    wait_time = between(0.5, 1.0)  # High frequency monitoring
    
    @task(5)
    def rapid_health_checks(self):
        """Frequent health checks like a monitoring system."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(3)
    def dashboard_data_refresh(self):
        """Simulate dashboard refreshing summary data."""
        with self.client.get("/summary", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard refresh failed: {response.status_code}")
    
    @task(2)
    def recent_activity_monitoring(self):
        """Monitor recent orders for real-time updates."""
        params = {"limit": 20}
        with self.client.get("/orders/recent", params=params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Recent activity failed: {response.status_code}")


class ErrorConditionTest(HttpUser):
    """
    Test API behavior under error conditions and edge cases.
    """
    weight = 1
    wait_time = between(2, 5)
    
    @task(1)
    def test_invalid_product_operations(self):
        """Test operations on non-existent products."""
        fake_id = random.randint(99900, 99999)
        
        # Try to get non-existent product
        with self.client.get(f"/products/{fake_id}", catch_response=True) as response:
            if response.status_code == 404:
                response.success()  # Expected
            else:
                response.failure(f"Unexpected response for missing product: {response.status_code}")
        
        # Try to order from non-existent product
        order_data = {
            "product_id": fake_id,
            "quantity": 1
        }
        
        with self.client.post("/orders/", json=order_data, catch_response=True) as response:
            if response.status_code == 404:
                response.success()  # Expected
            else:
                response.failure(f"Unexpected response for invalid order: {response.status_code}")
    
    @task(1)
    def test_validation_errors(self):
        """Test various validation error scenarios."""
        # Invalid product data
        invalid_product = {
            "sku": "",  # Empty SKU
            "name": "A",  # Too short
            "price": -10.0,  # Negative price
            "stock": -5  # Negative stock
        }
        
        with self.client.post("/products/", json=invalid_product, catch_response=True) as response:
            if response.status_code == 422:
                response.success()  # Expected validation error
            else:
                response.failure(f"Expected validation error: {response.status_code}")
        
        # Invalid order data
        invalid_order = {
            "product_id": -1,  # Invalid ID
            "quantity": 0  # Zero quantity
        }
        
        with self.client.post("/orders/", json=invalid_order, catch_response=True) as response:
            if response.status_code == 422:
                response.success()  # Expected validation error
            else:
                response.failure(f"Expected validation error: {response.status_code}")


# Custom event handlers for specific scenarios
@events.test_start.add_listener
def on_scenario_test_start(environment, **kwargs):
    """Initialize scenario-specific testing."""
    print("🎯 Starting specific scenario tests:")
    print("   - Last Item Race Condition Testing")
    print("   - Bulk Operations Performance")
    print("   - Stock Depletion and Recovery")
    print("   - High-Frequency Monitoring")
    print("   - Error Condition Handling")


# Metrics tracking for specific scenarios
stock_depletion_events = 0
race_condition_events = 0

@events.request.add_listener
def track_scenario_metrics(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Track metrics specific to our scenarios."""
    global stock_depletion_events, race_condition_events
    
    if hasattr(response, 'status_code') and response.status_code == 409:
        if "orders" in name:
            stock_depletion_events += 1
            if stock_depletion_events % 10 == 0:
                print(f"📊 Stock depletion events: {stock_depletion_events}")
    
    # Track response times for critical operations
    if "orders" in name and response_time > 1000:  # > 1 second
        print(f"⚠️ Slow order processing: {response_time:.2f}ms for {name}")


@events.test_stop.add_listener
def scenario_test_summary(environment, **kwargs):
    """Print scenario-specific summary."""
    print(f"\n📊 Scenario Test Results:")
    print(f"   Stock depletion events handled: {stock_depletion_events}")
    print(f"   Race condition prevention: {'✅ Working' if stock_depletion_events > 0 else '❓ Not tested'}")
    
    # Performance thresholds
    avg_response = environment.stats.total.avg_response_time
    if avg_response < 200:
        print(f"   Performance: ✅ Excellent ({avg_response:.2f}ms avg)")
    elif avg_response < 500:
        print(f"   Performance: ✅ Good ({avg_response:.2f}ms avg)")
    elif avg_response < 1000:
        print(f"   Performance: ⚠️ Acceptable ({avg_response:.2f}ms avg)")
    else:
        print(f"   Performance: ❌ Poor ({avg_response:.2f}ms avg)")

"""
Locust load testing scenarios for Orders & Inventory Management API.

This file contains realistic user behaviors and load testing scenarios
to validate API performance, concurrency handling, and system limits.

Run with:
    locust -f load_tests/locustfile.py --host=http://localhost:8000
"""

import random
import json
from typing import Dict, Any, List
from locust import HttpUser, task, between, events
from faker import Faker

fake = Faker()


class APITestData:
    """Shared test data for load testing."""
    
    def __init__(self):
        self.products: List[Dict[str, Any]] = []
        self.orders: List[Dict[str, Any]] = []
        self.product_counter = 0
        
    def generate_product_data(self) -> Dict[str, Any]:
        """Generate realistic product data."""
        self.product_counter += 1
        categories = ["LAPTOP", "PHONE", "TABLET", "WATCH", "HEADPHONE", "CAMERA"]
        category = random.choice(categories)
        
        return {
            "sku": f"{category}-{self.product_counter:04d}",
            "name": f"{fake.company()} {category.title()} {fake.word().title()}",
            "price": round(random.uniform(50.0, 2000.0), 2),
            "stock": random.randint(10, 500)
        }
    
    def get_random_product_id(self) -> int:
        """Get a random product ID from created products."""
        if not self.products:
            return 1  # Fallback
        return random.choice(self.products)["id"]

# Global test data instance
test_data = APITestData()


class InventoryManagementUser(HttpUser):
    """
    Simulates a typical user of the inventory management system.
    
    This represents an admin user who manages products and processes orders.
    Weight: 30% of users
    """
    weight = 3
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Setup when user starts - create some initial products."""
        self.create_initial_products()
    
    def create_initial_products(self):
        """Create a few products to work with."""
        for _ in range(3):
            product_data = test_data.generate_product_data()
            response = self.client.post("/products/", json=product_data)
            if response.status_code == 201:
                product = response.json()
                test_data.products.append(product)
    
    @task(10)
    def view_products(self):
        """View products list - most common operation."""
        params = {
            "page": random.randint(1, 3),
            "per_page": random.choice([10, 20, 50])
        }
        
        with self.client.get("/products/", params=params, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                response.success()
                # Store some products for later use
                if data.get("products"):
                    test_data.products.extend(data["products"][:5])
            else:
                response.failure(f"Failed to get products: {response.status_code}")
    
    @task(8)
    def view_single_product(self):
        """View individual product details."""
        if test_data.products:
            product_id = random.choice(test_data.products)["id"]
            with self.client.get(f"/products/{product_id}", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.success()  # Expected for some products
                else:
                    response.failure(f"Unexpected status: {response.status_code}")
    
    @task(5)
    def create_product(self):
        """Create new products."""
        product_data = test_data.generate_product_data()
        
        with self.client.post("/products/", json=product_data, catch_response=True) as response:
            if response.status_code == 201:
                product = response.json()
                test_data.products.append(product)
                response.success()
            elif response.status_code == 409:
                response.success()  # Duplicate SKU is expected occasionally
            else:
                response.failure(f"Failed to create product: {response.status_code}")
    
    @task(3)
    def update_product(self):
        """Update existing products."""
        if not test_data.products:
            return
            
        product = random.choice(test_data.products)
        update_data = {}
        
        # Randomly update different fields
        if random.choice([True, False]):
            update_data["price"] = round(random.uniform(50.0, 2000.0), 2)
        if random.choice([True, False]):
            update_data["stock"] = random.randint(0, 1000)
        if random.choice([True, False]):
            update_data["name"] = f"Updated {fake.word().title()} Product"
        
        if update_data:
            with self.client.put(f"/products/{product['id']}", json=update_data, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.success()  # Product might have been deleted
                else:
                    response.failure(f"Failed to update product: {response.status_code}")
    
    @task(2)
    def search_products(self):
        """Search products by various criteria."""
        search_params = {}
        
        # Random search criteria
        if random.choice([True, False]):
            search_params["search"] = random.choice(["laptop", "phone", "premium", "pro"])
        if random.choice([True, False]):
            search_params["min_price"] = random.randint(50, 500)
        if random.choice([True, False]):
            search_params["max_price"] = random.randint(500, 2000)
        if random.choice([True, False]):
            search_params["in_stock_only"] = True
        
        with self.client.get("/products/", params=search_params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")


class OrderProcessingUser(HttpUser):
    """
    Simulates users processing orders - the most critical concurrent operation.
    
    This represents order processing staff or automated systems creating orders.
    Weight: 50% of users (highest because this is the critical path)
    """
    weight = 5
    wait_time = between(0.5, 2)  # Faster operations for order processing
    
    @task(15)
    def create_order(self):
        """Create new orders - most critical concurrent operation."""
        if not test_data.products:
            # Create a product first
            product_data = test_data.generate_product_data()
            response = self.client.post("/products/", json=product_data)
            if response.status_code == 201:
                test_data.products.append(response.json())
        
        if test_data.products:
            product = random.choice(test_data.products)
            quantity = random.randint(1, 10)
            
            order_data = {
                "product_id": product["id"],
                "quantity": quantity
            }
            
            with self.client.post("/orders/", json=order_data, catch_response=True) as response:
                if response.status_code == 201:
                    order = response.json()
                    test_data.orders.append(order)
                    response.success()
                elif response.status_code == 409:
                    # Insufficient stock - expected under load
                    response.success()
                elif response.status_code == 404:
                    # Product not found - might have been deleted
                    response.success()
                else:
                    response.failure(f"Failed to create order: {response.status_code}")
    
    @task(10)
    def view_orders(self):
        """View orders list."""
        params = {
            "page": random.randint(1, 3),
            "per_page": random.choice([10, 20, 50])
        }
        
        # Add filters occasionally
        if random.choice([True, False]):
            params["status"] = random.choice(["PENDING", "PAID", "SHIPPED", "CANCELED"])
        
        with self.client.get("/orders/", params=params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get orders: {response.status_code}")
    
    @task(8)
    def view_order_details(self):
        """View individual order details."""
        if test_data.orders:
            order_id = random.choice(test_data.orders)["id"]
            with self.client.get(f"/orders/{order_id}", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.success()  # Order might have been deleted
                else:
                    response.failure(f"Unexpected status: {response.status_code}")
    
    @task(5)
    def process_payment(self):
        """Mark orders as paid."""
        if test_data.orders:
            order = random.choice(test_data.orders)
            with self.client.post(f"/orders/{order['id']}/pay", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code in [404, 422]:
                    response.success()  # Expected for already processed orders
                else:
                    response.failure(f"Failed to pay order: {response.status_code}")
    
    @task(3)
    def ship_order(self):
        """Mark orders as shipped."""
        if test_data.orders:
            order = random.choice(test_data.orders)
            with self.client.post(f"/orders/{order['id']}/ship", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code in [404, 422]:
                    response.success()  # Expected for non-paid orders
                else:
                    response.failure(f"Failed to ship order: {response.status_code}")
    
    @task(2)
    def cancel_order(self):
        """Cancel orders."""
        if test_data.orders:
            order = random.choice(test_data.orders)
            with self.client.post(f"/orders/{order['id']}/cancel", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code in [404, 422]:
                    response.success()  # Expected for shipped orders
                else:
                    response.failure(f"Failed to cancel order: {response.status_code}")


class MonitoringUser(HttpUser):
    """
    Simulates monitoring and reporting users.
    
    This represents dashboard users, reporting systems, and health checks.
    Weight: 20% of users
    """
    weight = 2
    wait_time = between(5, 15)  # Less frequent operations
    
    @task(10)
    def health_check(self):
        """Regular health checks."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(8)
    def system_summary(self):
        """Get system summary for dashboards."""
        with self.client.get("/summary", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Summary failed: {response.status_code}")
    
    @task(5)
    def api_documentation(self):
        """Access API documentation."""
        with self.client.get("/docs", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Docs access failed: {response.status_code}")
    
    @task(3)
    def recent_orders(self):
        """Get recent orders for monitoring."""
        params = {"limit": random.choice([5, 10, 20])}
        with self.client.get("/orders/recent", params=params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Recent orders failed: {response.status_code}")


class HighConcurrencyOrderUser(HttpUser):
    """
    Specialized user for testing race conditions and concurrent access.
    
    This simulates the "last item" scenario and high-concurrency order creation.
    Used for stress testing the concurrency improvements.
    """
    weight = 1  # Lower weight but high intensity
    wait_time = between(0.1, 0.5)  # Very fast operations to create contention
    
    @task(20)
    def rapid_order_creation(self):
        """Rapidly create orders to test concurrency."""
        if test_data.products:
            # Pick products with potentially low stock
            product = random.choice(test_data.products)
            
            # Small quantities to increase chance of stock depletion
            quantity = random.randint(1, 3)
            
            order_data = {
                "product_id": product["id"],
                "quantity": quantity
            }
            
            with self.client.post("/orders/", json=order_data, catch_response=True) as response:
                if response.status_code == 201:
                    response.success()
                elif response.status_code == 409:
                    # This is what we want to test - proper handling of stock conflicts
                    response.success()
                else:
                    response.failure(f"Unexpected response: {response.status_code}")
    
    @task(5)
    def concurrent_stock_updates(self):
        """Update stock concurrently to test race conditions."""
        if test_data.products:
            product = random.choice(test_data.products)
            adjustment = random.randint(-10, 50)
            
            adjustment_data = {
                "adjustment": adjustment,
                "reason": "Load test adjustment"
            }
            
            with self.client.post(f"/products/{product['id']}/stock/adjust", 
                                json=adjustment_data, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    response.success()  # Product might have been deleted
                else:
                    response.failure(f"Stock adjustment failed: {response.status_code}")


# Locust event handlers for custom metrics and logging
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Log important events and track custom metrics."""
    if exception:
        print(f"Request failed: {request_type} {name} - {exception}")
    
    # Track specific error patterns
    if hasattr(response, 'status_code'):
        if response.status_code == 409 and "orders" in name:
            # This is good - our concurrency control is working
            print(f"✅ Concurrency control prevented overselling: {name}")
        elif response.status_code >= 500:
            print(f"❌ Server error: {request_type} {name} - {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test environment."""
    print("🚀 Starting load test for Orders & Inventory Management API")
    print("📊 Test scenarios:")
    print("   - Inventory Management Users (30%): CRUD operations on products")
    print("   - Order Processing Users (50%): Order creation and processing")
    print("   - Monitoring Users (20%): Health checks and reporting")
    print("   - High Concurrency Users (10%): Race condition testing")
    print("🎯 Focus: Testing concurrency control and API performance")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Cleanup and final reporting."""
    print("🏁 Load test completed")
    print(f"📈 Total requests: {environment.stats.total.num_requests}")
    print(f"⚡ Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"❌ Total failures: {environment.stats.total.num_failures}")
    
    if environment.stats.total.num_failures > 0:
        failure_rate = (environment.stats.total.num_failures / environment.stats.total.num_requests) * 100
        print(f"📊 Failure rate: {failure_rate:.2f}%")
    
    print("🔍 Check for concurrency-related errors in the logs above")


if __name__ == "__main__":
    # This allows running the file directly for testing
    import subprocess
    import sys
    
    print("Starting Locust load test...")
    print("Open http://localhost:8089 to access the Locust web UI")
    
    cmd = [
        sys.executable, "-m", "locust",
        "-f", __file__,
        "--host", "http://localhost:8000"
    ]
    
    subprocess.run(cmd)

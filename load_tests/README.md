# Load Testing with Locust

This directory contains comprehensive load testing scenarios for the Orders & Inventory Management API using Locust.

## 🎯 What We're Testing

### Core Performance Metrics
- **Response Times**: API response latency under load
- **Throughput**: Requests per second the API can handle
- **Concurrency**: Behavior under concurrent access
- **Race Conditions**: "Last item" scenarios and stock management
- **Error Handling**: API behavior under stress and invalid inputs

### Critical Business Scenarios
- **Order Creation**: The most critical concurrent operation
- **Stock Management**: Preventing overselling and negative stock
- **Bulk Operations**: High-throughput batch processing
- **System Monitoring**: Health checks and dashboard access

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Install Locust and testing dependencies
poetry install

# Or with pip
pip install locust faker
```

### 2. Start Your API
```bash
# Terminal 1: Start the API server
python run_api.py
```

### 3. Run Load Tests
```bash
# Terminal 2: Start Locust
locust -f load_tests/locustfile.py --host=http://localhost:8000

# Or run specific scenarios
locust -f load_tests/scenarios.py --host=http://localhost:8000
```

### 4. Access Locust Web UI
Open http://localhost:8089 in your browser to:
- Configure number of users and spawn rate
- Monitor real-time performance metrics
- View detailed response time charts
- Download test results

## 📊 Test Scenarios

### Main Load Test (`locustfile.py`)

#### User Types & Distribution:
- **Inventory Management Users (30%)**: Product CRUD operations
- **Order Processing Users (50%)**: Order creation and processing
- **Monitoring Users (20%)**: Health checks and reporting
- **High Concurrency Users (10%)**: Race condition testing

#### Realistic Behaviors:
- **Product Management**: Create, read, update, search products
- **Order Processing**: Create orders, process payments, ship orders
- **System Monitoring**: Health checks, summaries, documentation access
- **Concurrent Access**: Rapid order creation to test race conditions

### Specialized Scenarios (`scenarios.py`)

#### 1. Last Item Race Condition Test
```python
# Tests concurrent access to limited stock
- Creates product with only 5 items
- Multiple users try to order simultaneously
- Validates concurrency control prevents overselling
```

#### 2. Bulk Operations Test
```python
# Tests high-throughput batch processing
- Rapid product creation (5 products at once)
- Bulk order processing
- System performance under sustained load
```

#### 3. Stock Depletion Recovery Test
```python
# Tests stock depletion and restocking scenarios
- Gradually depletes product stock through orders
- Periodically restocks products
- Tests system behavior during stock transitions
```

#### 4. High-Frequency Monitoring Test
```python
# Tests real-time monitoring systems
- Rapid health checks (every 0.5-1 second)
- Dashboard data refreshing
- Recent activity monitoring
```

#### 5. Error Condition Test
```python
# Tests API resilience under error conditions
- Invalid product operations (404 scenarios)
- Validation errors (422 scenarios)
- Edge cases and boundary conditions
```

## 🎛️ Configuration Options

### Basic Load Test
```bash
# Light load testing
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
       --users 10 --spawn-rate 2 --run-time 2m

# Medium load testing
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
       --users 50 --spawn-rate 5 --run-time 5m

# Heavy load testing
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
       --users 200 --spawn-rate 10 --run-time 10m
```

### Headless Mode (CI/CD)
```bash
# Run without web UI for automated testing
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
       --users 50 --spawn-rate 5 --run-time 3m --headless \
       --html results.html --csv results
```

### Specific Scenario Testing
```bash
# Test only race conditions
locust -f load_tests/scenarios.py --host=http://localhost:8000 \
       -u 20 -r 5 -t 60s

# Test bulk operations
locust -f load_tests/scenarios.py --host=http://localhost:8000 \
       -u 10 -r 2 -t 120s
```

## 📈 Performance Expectations

### Response Time Targets
- **GET requests**: < 200ms average
- **POST/PUT requests**: < 500ms average
- **Complex operations**: < 1000ms average

### Throughput Targets
- **Light load**: 100+ requests/second
- **Medium load**: 300+ requests/second
- **Heavy load**: 500+ requests/second

### Concurrency Targets
- **Race condition prevention**: 0% overselling events
- **Error rate**: < 1% under normal load
- **Stock consistency**: No negative stock values

## 🔍 Monitoring & Analysis

### Key Metrics to Watch
1. **Response Times**: 50th, 95th, 99th percentiles
2. **Error Rates**: By status code and endpoint
3. **Throughput**: Requests per second over time
4. **Concurrency Events**: Stock depletion handling
5. **Resource Usage**: CPU, memory, database connections

### Common Performance Issues
```bash
# Slow response times
- Check database query performance
- Monitor connection pool usage
- Verify proper indexing

# High error rates
- Check for race conditions in order creation
- Validate input sanitization
- Monitor resource exhaustion

# Concurrency problems
- Look for negative stock values
- Check transaction isolation levels
- Verify atomic operations
```

### Success Criteria
- ✅ **No overselling**: All stock constraints respected
- ✅ **Stable performance**: Response times remain consistent
- ✅ **Error handling**: Graceful degradation under load
- ✅ **System resilience**: Recovery from stress conditions

## 🐛 Troubleshooting

### Common Issues
```bash
# Connection refused
- Ensure API is running on http://localhost:8000
- Check firewall and port availability

# High failure rates
- Verify API endpoints are correct
- Check for database connectivity issues
- Monitor system resource usage

# Inconsistent results
- Use consistent test data
- Account for database state between runs
- Ensure proper test isolation
```

### Debug Mode
```bash
# Run with verbose logging
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
       --loglevel DEBUG

# Single user for debugging
locust -f load_tests/locustfile.py --host=http://localhost:8000 \
       --users 1 --spawn-rate 1
```

## 📊 Results Analysis

### Interpreting Results
1. **Green metrics**: System performing well
2. **Yellow metrics**: Performance degradation detected
3. **Red metrics**: System under stress or failing

### Performance Baselines
- **Development**: Single user, all operations < 100ms
- **Staging**: 10 users, 95th percentile < 500ms
- **Production**: 100+ users, 99th percentile < 1000ms

### Load Testing Best Practices
- Start with light load and gradually increase
- Run tests for sufficient duration (5+ minutes)
- Monitor both API and database performance
- Test realistic user behavior patterns
- Validate business logic under stress

## 🚀 Advanced Usage

### Custom Scenarios
Create your own test scenarios by extending the base classes:

```python
from locust import HttpUser, task, between

class CustomUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def custom_behavior(self):
        # Your custom test logic here
        pass
```

### Integration with CI/CD
```yaml
# Example GitHub Actions integration
- name: Load Testing
  run: |
    locust -f load_tests/locustfile.py \
           --host=http://staging-api:8000 \
           --users 50 --spawn-rate 5 --run-time 3m \
           --headless --html results.html
    
    # Upload results as artifacts
    upload-artifact results.html
```

This comprehensive load testing setup ensures your API can handle real-world traffic patterns while maintaining data integrity and performance! 🎯

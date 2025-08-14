# 🚀 Load Testing Demo with Locust

This guide shows you how to use the comprehensive load testing setup to validate your API's performance and concurrency handling.

## 🎯 What You'll Test

### Critical Performance Areas
- **Race Conditions**: Multiple users ordering the last item
- **Concurrency Control**: Atomic stock management
- **API Performance**: Response times under load
- **System Limits**: Maximum throughput and user capacity
- **Error Handling**: Graceful degradation under stress

## 📋 Prerequisites

1. **Install Dependencies**:
   ```bash
   poetry install
   # This installs locust and faker for load testing
   ```

2. **Start Your API**:
   ```bash
   # Terminal 1: Start the API
   python run_api.py
   
   # Verify it's running
   curl http://localhost:8000/health
   ```

## 🚀 Quick Start Demo

### 1. Quick Smoke Test (2 minutes)
```bash
# Terminal 2: Run a quick load test
./scripts/run_load_tests.sh quick

# This will:
# - Test with 10 concurrent users
# - Run for 2 minutes
# - Generate HTML report
# - Test basic API functionality
```

### 2. Interactive Testing
```bash
# Start Locust web UI for interactive testing
./scripts/run_load_tests.sh interactive

# Then open: http://localhost:8089
# Configure: 20 users, spawn rate 5, host: http://localhost:8000
# Click "Start swarming" and watch real-time metrics
```

### 3. Race Condition Testing
```bash
# Test the critical "last item" scenario
./scripts/run_load_tests.sh race

# This specifically tests:
# - Multiple users ordering limited stock items
# - Concurrency control effectiveness
# - Prevention of overselling
```

## 📊 Understanding the Results

### Key Metrics to Watch

#### ✅ **Good Performance Indicators**
- **Response Times**: < 200ms average for GET, < 500ms for POST
- **Error Rate**: < 1% under normal load
- **Race Condition Prevention**: 0 overselling events
- **Throughput**: 100+ requests/second

#### ⚠️ **Warning Signs**
- Response times > 1000ms consistently
- Error rates > 5%
- Memory usage continuously increasing
- Database connection exhaustion

#### ❌ **Critical Issues**
- Negative stock values (race condition failure)
- Response times > 5000ms
- Error rates > 20%
- System crashes or timeouts

### Sample Results Analysis

```bash
# After running a test, check the results:
ls load_test_results/

# Example output:
# quick_test_20231201_143022.html    # Visual report
# quick_test_20231201_143022.csv     # Raw data
# quick_test_20231201_143022.log     # Detailed logs
```

**HTML Report Sections**:
- **Statistics**: Request counts, response times, error rates
- **Charts**: Response time distribution, requests per second
- **Failures**: Detailed error breakdown
- **Download Data**: CSV export for further analysis

## 🎯 Specific Test Scenarios

### Scenario 1: Last Item Race Condition
```bash
# What it tests:
# - Creates product with only 5 items in stock
# - 20 users simultaneously try to order
# - Validates only 5 orders succeed (no overselling)

./scripts/run_load_tests.sh race

# Expected results:
# ✅ Exactly 5 successful orders
# ✅ 15 "insufficient stock" errors (HTTP 409)
# ✅ Final stock = 0 (not negative)
```

### Scenario 2: Standard Load Test
```bash
# What it tests:
# - 50 concurrent users for 5 minutes
# - Mix of product management and order processing
# - Realistic user behavior patterns

./scripts/run_load_tests.sh standard

# Expected results:
# ✅ Average response time < 500ms
# ✅ 95th percentile < 1000ms
# ✅ Error rate < 1%
# ✅ 300+ requests/second throughput
```

### Scenario 3: Stress Test
```bash
# What it tests:
# - 200 concurrent users for 10 minutes
# - System behavior at high load
# - Performance degradation patterns

./scripts/run_load_tests.sh stress

# Watch for:
# ⚠️ Response time increases
# ⚠️ Higher error rates (still < 5%)
# ⚠️ Resource usage patterns
```

## 🔍 Real-Time Monitoring

### During Interactive Testing
1. **Open Locust UI**: http://localhost:8089
2. **Configure Load**: Start with 10 users, spawn rate 2
3. **Monitor Metrics**:
   - **RPS**: Requests per second (target: 50+)
   - **Response Time**: Median and 95th percentile
   - **Error Rate**: Percentage of failed requests
   - **Active Users**: Current simulated user count

### API Health Monitoring
```bash
# Monitor API health during tests
watch -n 2 "curl -s http://localhost:8000/health | jq"

# Monitor system summary
watch -n 5 "curl -s http://localhost:8000/summary | jq"
```

## 🐛 Troubleshooting Common Issues

### High Error Rates
```bash
# Check API logs for errors
tail -f api.log

# Common causes:
# - Database connection limits
# - Memory exhaustion
# - Validation errors in test data
```

### Slow Response Times
```bash
# Check system resources
top -p $(pgrep -f "python run_api.py")

# Common causes:
# - Database query performance
# - Lack of proper indexing
# - Resource contention
```

### Race Condition Failures
```bash
# Look for negative stock values
curl http://localhost:8000/products/ | jq '.products[] | select(.stock < 0)'

# Should return empty if concurrency control works
```

## 📈 Performance Optimization Tips

### Database Optimization
```python
# Add indexes for common queries
CREATE INDEX idx_product_sku ON products(sku);
CREATE INDEX idx_order_product_status ON orders(product_id, status);
CREATE INDEX idx_order_created_at ON orders(created_at);
```

### API Performance
```python
# Use connection pooling
engine = create_engine(
    database_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30
)

# Add response caching for read-heavy endpoints
@app.get("/products/")
@cache(expire=60)  # Cache for 1 minute
async def list_products():
    # ...
```

### Concurrency Improvements
```python
# Use async endpoints for I/O bound operations
@app.get("/products/")
async def list_products_async():
    # Non-blocking database calls
    async with AsyncSession(engine) as session:
        # ...
```

## 🚀 Advanced Testing Scenarios

### Complete Test Suite
```bash
# Run all tests in sequence (30+ minutes)
./scripts/run_load_tests.sh all

# Includes:
# 1. Smoke test (quick validation)
# 2. Standard load (normal traffic)
# 3. Concurrency test (race conditions)
# 4. Stress test (system limits)
```

### Custom Test Configuration
```bash
# Run custom test with specific parameters
locust -f load_tests/locustfile.py \
       --host=http://localhost:8000 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 5m \
       --headless \
       --html custom_results.html
```

### CI/CD Integration
```yaml
# Example GitHub Actions step
- name: Load Testing
  run: |
    python run_api.py &
    sleep 10  # Wait for API to start
    ./scripts/run_load_tests.sh quick
    kill %1  # Stop API
```

## 🎯 Success Criteria

### Performance Benchmarks
- **Light Load (10 users)**: All operations < 100ms
- **Normal Load (50 users)**: 95th percentile < 500ms  
- **Heavy Load (200 users)**: 99th percentile < 2000ms

### Concurrency Validation
- **No Overselling**: Stock never goes negative
- **Atomic Operations**: Order creation prevents race conditions
- **Consistent State**: Database integrity maintained

### System Reliability
- **Error Handling**: Graceful degradation under stress
- **Recovery**: System returns to normal after load
- **Stability**: No memory leaks or resource exhaustion

## 📊 Sample Test Results

### Successful Load Test
```
Type     Name                                          # reqs      # fails
GET      /health                                       1,245           0
GET      /products/                                    2,890          12
POST     /orders/                                      1,567          23
POST     /orders/{id}/pay                                987           5

Total requests: 6,689
Failures: 40 (0.6%)
Average response time: 245ms
95th percentile: 890ms
RPS: 22.3

✅ Race Condition Test: 0 overselling events detected
✅ Performance: Within acceptable limits
✅ Error Rate: Below 1% threshold
```

This comprehensive load testing setup ensures your API can handle real-world traffic while maintaining data integrity and performance! 🎯

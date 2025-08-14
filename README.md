# 📦 Orders & Inventory Management System (OIMS)

A comprehensive REST API for managing products and orders with real-time inventory tracking, automated business workflows, and production-ready deployment.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Poetry (recommended) or pip

### Installation
```bash
# Create Python environment
conda create -n oims python=3.12
conda activate oims

# Install dependencies
poetry install
# OR with pip
pip install -r requirements.txt
```

### Run the API
```bash
# Start the development server
python run_api.py

# API will be available at:
# - Main API: http://localhost:8000
# - Interactive Docs: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
```

## 🎯 Key Features

### Core Functionality
- **Product Management**: Full CRUD operations with SKU validation
- **Order Processing**: Complete order lifecycle with status transitions
- **Inventory Tracking**: Real-time stock management with concurrency control
- **Race Condition Prevention**: Atomic operations for "last item" scenarios

### API Capabilities
- **RESTful Endpoints**: Products, Orders, Health checks, System summary
- **Interactive Documentation**: Swagger UI with examples and validation
- **Error Handling**: Comprehensive error responses with detailed messages
- **Pagination**: Efficient data retrieval for large datasets
- **Search & Filtering**: Advanced product search and order filtering

### Performance & Testing
- **Load Testing**: Comprehensive Locust test suites for performance validation
- **Concurrency Testing**: Specialized tests for race conditions and stock management
- **Production Ready**: Optimized for deployment with monitoring and health checks

## 🧪 Testing

### Run Unit Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/orders_inventory
```

### Load Testing
```bash
# Quick load test (2 minutes)
./scripts/run_load_tests.sh quick

# Interactive load testing with web UI
./scripts/run_load_tests.sh interactive
# Open http://localhost:8089 for web UI

# Complete test suite
./scripts/run_load_tests.sh all
```

## 🚀 Deployment

### Render.com Deployment
Ready for one-click deployment to Render.com with Infrastructure as Code:

```bash
# Prepare for deployment
./scripts/deploy_to_render.sh deploy

# Then go to render.com and deploy using the render.yaml configuration
```

**Deployment Features:**
- **Infrastructure as Code**: Complete `render.yaml` configuration
- **Environment Variables**: Production-ready configuration
- **Auto-scaling**: Configured for production load
- **Health Monitoring**: Built-in health checks and monitoring

### Manual Deployment
For other platforms, use these commands:
- **Build**: `pip install poetry && poetry config virtualenvs.create false && poetry install --only=main`
- **Start**: `uvicorn src.orders_inventory.api.main:app --host 0.0.0.0 --port $PORT`

## 📚 Documentation

- **[Deployment Guide](DEPLOYMENT.md)**: Complete Render.com deployment instructions
- **[Load Testing Guide](load_tests/README.md)**: Performance testing with Locust
- **[Load Testing Demo](LOAD_TESTING_DEMO.md)**: Step-by-step testing walkthrough
- **[Concurrency Analysis](docs/concurrency_analysis.md)**: Race condition handling details

## 🏗️ Project Structure

```
orders-inventory/
├── src/orders_inventory/          # Main application package
│   ├── api/                       # FastAPI application
│   ├── models/                    # Data models (SQLModel)
│   ├── repositories/              # Data access layer
│   ├── services/                  # Business logic
│   └── utils/                     # Utilities and exceptions
├── tests/                         # Test suite (mirrors src structure)
├── load_tests/                    # Load testing scenarios
├── scripts/                       # Deployment and utility scripts
├── docs/                          # Additional documentation
├── render.yaml                    # Render.com deployment config
└── requirements.txt               # Production dependencies
```

## 🛠️ Development

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Database Management
```bash
# Initialize database (automatic on startup)
python -c "from src.orders_inventory.utils.database import init_database; init_database()"
```

## 📊 API Endpoints

### Products
- `GET /products/` - List products with pagination and search
- `POST /products/` - Create new product
- `GET /products/{id}` - Get product details
- `PUT /products/{id}` - Update product (partial updates supported)
- `DELETE /products/{id}` - Delete product

### Orders
- `GET /orders/` - List orders with filtering
- `POST /orders/` - Create new order (atomic stock reduction)
- `GET /orders/{id}` - Get order details
- `POST /orders/{id}/pay` - Mark order as paid
- `POST /orders/{id}/ship` - Mark order as shipped
- `POST /orders/{id}/cancel` - Cancel order

### System
- `GET /health` - Health check and system status
- `GET /summary` - System summary and metrics
- `GET /docs` - Interactive API documentation

## 🔧 Configuration

### Environment Variables
- `DATABASE_URL`: Database connection string (default: SQLite)
- `ENVIRONMENT`: Application environment (development/production)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `CORS_ORIGINS`: Allowed CORS origins for frontend integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Performance Targets

- **Response Times**: < 200ms for GET, < 500ms for POST operations
- **Throughput**: 100+ requests/second under normal load
- **Concurrency**: Zero overselling events, perfect stock consistency
- **Availability**: 99.9% uptime with health monitoring

**Ready for production deployment with comprehensive testing and monitoring!** 🚀
"""Shared test fixtures and configuration."""

import pytest
from decimal import Decimal
from sqlmodel import Session, create_engine, SQLModel

from orders_inventory.models import Product, Order, OrderStatus
from orders_inventory.repositories import ProductRepository, OrderRepository
from orders_inventory.services import InventoryService, OrderService


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture
def sample_product():
    """Create a sample product for testing."""
    return Product(
        sku="TEST001",
        name="Test Product",
        price=Decimal("19.99"),
        stock=100
    )


@pytest.fixture
def sample_products():
    """Create multiple sample products for testing."""
    return [
        Product(
            sku="PROD001",
            name="Product One",
            price=Decimal("10.00"),
            stock=50
        ),
        Product(
            sku="PROD002", 
            name="Product Two",
            price=Decimal("25.99"),
            stock=30
        ),
        Product(
            sku="PROD003",
            name="Product Three",
            price=Decimal("5.50"),
            stock=0  # Out of stock
        )
    ]


@pytest.fixture
def product_repository(test_session):
    """Create a product repository for testing."""
    return ProductRepository(test_session)


@pytest.fixture
def order_repository(test_session):
    """Create an order repository for testing."""
    return OrderRepository(test_session)


@pytest.fixture
def inventory_service(test_session):
    """Create an inventory service for testing."""
    return InventoryService(test_session)


@pytest.fixture
def order_service(test_session):
    """Create an order service for testing."""
    return OrderService(test_session)


@pytest.fixture
def created_product(product_repository, sample_product):
    """Create and return a product saved in the database."""
    return product_repository.create(sample_product)


@pytest.fixture
def created_products(product_repository, sample_products):
    """Create and return multiple products saved in the database."""
    created = []
    for product in sample_products:
        created.append(product_repository.create(product))
    return created


@pytest.fixture
def sample_order(created_product):
    """Create a sample order for testing."""
    return Order(
        product_id=created_product.id,
        quantity=5,
        status=OrderStatus.PENDING
    )


@pytest.fixture
def created_order(order_repository, sample_order):
    """Create and return an order saved in the database."""
    return order_repository.create(sample_order)

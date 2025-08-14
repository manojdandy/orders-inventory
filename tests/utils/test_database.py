"""Tests for database utilities."""

import pytest
from sqlmodel import Session, SQLModel

from orders_inventory.utils.database import (
    get_db_session,
    init_database,
    reset_database,
    get_database_info
)


class TestDatabaseUtils:
    """Test database utility functions."""
    
    def test_get_db_session(self):
        """Test getting database session."""
        session = get_db_session()
        assert isinstance(session, Session)
        session.close()
    
    def test_init_database_default(self):
        """Test initializing database with default settings."""
        # This should not raise any errors
        init_database()
    
    def test_init_database_custom_url(self):
        """Test initializing database with custom URL."""
        # Test with in-memory SQLite
        init_database("sqlite:///:memory:")
    
    def test_get_database_info(self):
        """Test getting database information."""
        info = get_database_info()
        
        assert "database_url" in info
        assert "engine" in info
        assert "is_sqlite" in info
        
        assert isinstance(info["database_url"], str)
        assert isinstance(info["engine"], str)
        assert isinstance(info["is_sqlite"], bool)
        
        # Should detect SQLite
        assert info["is_sqlite"] is True
    
    def test_reset_database(self):
        """Test resetting database."""
        # Create some test data first
        from orders_inventory.models import Product
        from orders_inventory.repositories import ProductRepository
        
        session = get_db_session()
        try:
            # Ensure tables exist
            init_database()
            
            # Add a product
            repo = ProductRepository(session)
            product = Product(sku="RESET001", name="Reset Test", price=10.00, stock=50)
            repo.create(product)
            
            # Verify product exists
            products = repo.get_all()
            assert len(products) >= 1
            
            session.commit()
        finally:
            session.close()
        
        # Reset database
        reset_database()
        
        # Verify data is gone
        session = get_db_session()
        try:
            repo = ProductRepository(session)
            products = repo.get_all()
            assert len(products) == 0
        finally:
            session.close()


class TestDatabaseIntegration:
    """Test database integration with models."""
    
    @pytest.fixture
    def temp_db_session(self):
        """Create a temporary database session for testing."""
        # Use in-memory database for isolation
        init_database("sqlite:///:memory:")
        session = get_db_session()
        yield session
        session.close()
    
    def test_create_and_query_product(self, temp_db_session):
        """Test creating and querying products in database."""
        from orders_inventory.models import Product
        from orders_inventory.repositories import ProductRepository
        
        repo = ProductRepository(temp_db_session)
        
        # Create product
        product = Product(sku="DB001", name="Database Test", price=15.99, stock=30)
        created = repo.create(product)
        
        assert created.id is not None
        assert created.sku == "DB001"
        
        # Query product
        retrieved = repo.get_by_sku("DB001")
        assert retrieved is not None
        assert retrieved.id == created.id
    
    def test_create_and_query_order(self, temp_db_session):
        """Test creating and querying orders in database."""
        from orders_inventory.models import Product, Order, OrderStatus
        from orders_inventory.repositories import ProductRepository, OrderRepository
        
        # Create product first
        product_repo = ProductRepository(temp_db_session)
        product = Product(sku="ORD001", name="Order Test", price=25.00, stock=100)
        created_product = product_repo.create(product)
        
        # Create order
        order_repo = OrderRepository(temp_db_session)
        order = Order(product_id=created_product.id, quantity=5, status=OrderStatus.PENDING)
        created_order = order_repo.create(order)
        
        assert created_order.id is not None
        assert created_order.product_id == created_product.id
        assert created_order.quantity == 5
        
        # Query order
        retrieved = order_repo.get_by_id(created_order.id)
        assert retrieved is not None
        assert retrieved.product_id == created_product.id
    
    def test_database_constraints(self, temp_db_session):
        """Test database constraints are enforced."""
        from orders_inventory.models import Product
        from orders_inventory.repositories import ProductRepository
        from sqlalchemy.exc import IntegrityError
        
        repo = ProductRepository(temp_db_session)
        
        # Create product with unique SKU
        product1 = Product(sku="UNIQUE001", name="First Product", price=10.00, stock=50)
        repo.create(product1)
        
        # Try to create another product with same SKU
        product2 = Product(sku="UNIQUE001", name="Second Product", price=15.00, stock=30)
        
        with pytest.raises(IntegrityError):
            repo.create(product2)
            temp_db_session.commit()
    
    def test_foreign_key_constraint(self, temp_db_session):
        """Test foreign key constraints are enforced."""
        from orders_inventory.models import Order
        from orders_inventory.repositories import OrderRepository
        from sqlalchemy.exc import IntegrityError
        
        order_repo = OrderRepository(temp_db_session)
        
        # Try to create order with non-existent product_id
        order = Order(product_id=99999, quantity=5)
        
        with pytest.raises(IntegrityError):
            order_repo.create(order)
            temp_db_session.commit()

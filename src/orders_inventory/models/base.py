"""Base database configuration and setup."""

from sqlmodel import SQLModel, create_engine, Session


class DatabaseConfig:
    """Database configuration and setup."""
    
    def __init__(self, database_url: str = "sqlite:///orders_inventory.db"):
        """Initialize database configuration.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
        )
    
    def create_tables(self):
        """Create all tables in the database."""
        SQLModel.metadata.create_all(self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        return Session(self.engine)
    
    def drop_tables(self):
        """Drop all tables (useful for testing)."""
        SQLModel.metadata.drop_all(self.engine)


# Default database instance
db_config = DatabaseConfig()


def get_db_session() -> Session:
    """Get a database session (convenience function)."""
    return db_config.get_session()


def init_database():
    """Initialize the database with tables."""
    db_config.create_tables()

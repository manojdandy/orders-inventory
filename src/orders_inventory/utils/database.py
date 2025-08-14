"""Database utilities and helper functions."""

from sqlmodel import Session
from ..models.base import db_config


def get_db_session() -> Session:
    """Get a database session (convenience function).
    
    Returns:
        Database session
    """
    return db_config.get_session()


def init_database(database_url: str = None):
    """Initialize the database with tables.
    
    Args:
        database_url: Optional database URL override
    """
    if database_url:
        # Create new config with custom URL
        from ..models.base import DatabaseConfig
        custom_config = DatabaseConfig(database_url)
        custom_config.create_tables()
    else:
        db_config.create_tables()


def reset_database():
    """Reset database by dropping and recreating all tables.
    
    WARNING: This will delete all data!
    """
    db_config.drop_tables()
    db_config.create_tables()


def get_database_info() -> dict:
    """Get information about the database configuration.
    
    Returns:
        Dictionary with database info
    """
    return {
        "database_url": db_config.database_url,
        "engine": str(db_config.engine),
        "is_sqlite": "sqlite" in db_config.database_url.lower()
    }

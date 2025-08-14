"""Base repository class with common operations."""

from typing import TypeVar, Generic, Type, Optional, List
from sqlmodel import Session, SQLModel, select

T = TypeVar('T', bound=SQLModel)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: Session, model: Type[T]):
        """Initialize repository with session and model type.
        
        Args:
            session: Database session
            model: SQLModel class
        """
        self.session = session
        self.model = model
    
    def create(self, entity: T) -> T:
        """Create a new entity."""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
    
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """Get entity by ID."""
        return self.session.get(self.model, entity_id)
    
    def get_all(self) -> List[T]:
        """Get all entities."""
        statement = select(self.model)
        return list(self.session.exec(statement).all())
    
    def update(self, entity: T) -> T:
        """Update an existing entity."""
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
    
    def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID."""
        entity = self.session.get(self.model, entity_id)
        if entity:
            self.session.delete(entity)
            self.session.commit()
            return True
        return False
    
    def count(self) -> int:
        """Count total entities."""
        statement = select(self.model)
        return len(list(self.session.exec(statement).all()))

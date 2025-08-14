"""FastAPI dependencies for dependency injection."""

from fastapi import Depends
from sqlmodel import Session

from ..models.base import get_db_session
from ..services import InventoryService, OrderService


def get_inventory_service(session: Session = Depends(get_db_session)) -> InventoryService:
    """Get inventory service instance."""
    return InventoryService(session)


def get_order_service(session: Session = Depends(get_db_session)) -> OrderService:
    """Get order service instance."""
    return OrderService(session)

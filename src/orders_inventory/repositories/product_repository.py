"""Product repository for data access operations."""

from typing import List, Optional
from sqlmodel import Session, select

from ..models import Product
from .base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository for Product operations."""
    
    def __init__(self, session: Session):
        super().__init__(session, Product)
    
    def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        statement = select(Product).where(Product.sku == sku.upper())
        return self.session.exec(statement).first()
    
    def search_by_name(self, name_pattern: str) -> List[Product]:
        """Search products by name pattern."""
        statement = select(Product).where(Product.name.contains(name_pattern))
        return list(self.session.exec(statement).all())
    
    def get_low_stock(self, threshold: int = 10) -> List[Product]:
        """Get products with stock below threshold."""
        statement = select(Product).where(Product.stock < threshold)
        return list(self.session.exec(statement).all())
    
    def get_by_price_range(self, min_price: float, max_price: float) -> List[Product]:
        """Get products within price range."""
        statement = select(Product).where(
            Product.price >= min_price,
            Product.price <= max_price
        )
        return list(self.session.exec(statement).all())
    
    def get_in_stock(self) -> List[Product]:
        """Get products that are in stock (stock > 0)."""
        statement = select(Product).where(Product.stock > 0)
        return list(self.session.exec(statement).all())
    
    def get_out_of_stock(self) -> List[Product]:
        """Get products that are out of stock (stock = 0)."""
        statement = select(Product).where(Product.stock == 0)
        return list(self.session.exec(statement).all())

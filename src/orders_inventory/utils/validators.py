"""Validation utilities for data validation."""

import re
from decimal import Decimal
from typing import Optional

from .exceptions import ValidationError


def validate_sku(sku: str) -> str:
    """Validate and normalize SKU.
    
    Args:
        sku: SKU to validate
        
    Returns:
        Normalized SKU (uppercase, trimmed)
        
    Raises:
        ValidationError: If SKU is invalid
    """
    if not sku or not isinstance(sku, str):
        raise ValidationError("SKU must be a non-empty string")
    
    sku = sku.strip()
    if not sku:
        raise ValidationError("SKU cannot be empty or whitespace only")
    
    if len(sku) > 50:
        raise ValidationError("SKU cannot exceed 50 characters")
    
    # Check for invalid characters (optional - can be customized)
    if not re.match(r'^[A-Z0-9_-]+$', sku.upper()):
        raise ValidationError("SKU can only contain letters, numbers, hyphens, and underscores")
    
    return sku.upper()


def validate_price(price) -> Decimal:
    """Validate and convert price to Decimal.
    
    Args:
        price: Price to validate (float, int, str, or Decimal)
        
    Returns:
        Price as Decimal
        
    Raises:
        ValidationError: If price is invalid
    """
    try:
        if isinstance(price, str):
            price_decimal = Decimal(price)
        elif isinstance(price, (int, float)):
            price_decimal = Decimal(str(price))
        elif isinstance(price, Decimal):
            price_decimal = price
        else:
            raise ValidationError(f"Price must be a number, got {type(price)}")
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid price format: {e}")
    
    if price_decimal <= 0:
        raise ValidationError("Price must be greater than 0")
    
    # Check for reasonable precision (2 decimal places)
    if price_decimal.as_tuple().exponent < -2:
        raise ValidationError("Price cannot have more than 2 decimal places")
    
    return price_decimal


def validate_stock(stock) -> int:
    """Validate stock quantity.
    
    Args:
        stock: Stock quantity to validate
        
    Returns:
        Stock as integer
        
    Raises:
        ValidationError: If stock is invalid
    """
    if not isinstance(stock, int):
        try:
            stock = int(stock)
        except (ValueError, TypeError):
            raise ValidationError(f"Stock must be an integer, got {type(stock)}")
    
    if stock < 0:
        raise ValidationError("Stock cannot be negative")
    
    # Check for reasonable maximum (optional business rule)
    if stock > 1000000:
        raise ValidationError("Stock quantity exceeds maximum allowed (1,000,000)")
    
    return stock


def validate_quantity(quantity) -> int:
    """Validate order quantity.
    
    Args:
        quantity: Quantity to validate
        
    Returns:
        Quantity as integer
        
    Raises:
        ValidationError: If quantity is invalid
    """
    if not isinstance(quantity, int):
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            raise ValidationError(f"Quantity must be an integer, got {type(quantity)}")
    
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than 0")
    
    # Check for reasonable maximum (optional business rule)
    if quantity > 10000:
        raise ValidationError("Order quantity exceeds maximum allowed (10,000)")
    
    return quantity


def validate_product_name(name: str) -> str:
    """Validate product name.
    
    Args:
        name: Product name to validate
        
    Returns:
        Validated and trimmed name
        
    Raises:
        ValidationError: If name is invalid
    """
    if not name or not isinstance(name, str):
        raise ValidationError("Product name must be a non-empty string")
    
    name = name.strip()
    if not name:
        raise ValidationError("Product name cannot be empty or whitespace only")
    
    if len(name) > 200:
        raise ValidationError("Product name cannot exceed 200 characters")
    
    if len(name) < 2:
        raise ValidationError("Product name must be at least 2 characters long")
    
    return name


def validate_email(email: Optional[str]) -> Optional[str]:
    """Validate email format (for future customer features).
    
    Args:
        email: Email to validate
        
    Returns:
        Validated email or None
        
    Raises:
        ValidationError: If email format is invalid
    """
    if not email:
        return None
    
    email = email.strip().lower()
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")
    
    return email

"""Custom exceptions for orders_inventory package."""


class OrdersInventoryError(Exception):
    """Base exception for orders_inventory package."""
    pass


class ProductNotFoundError(OrdersInventoryError):
    """Raised when a product is not found."""
    pass


class OrderNotFoundError(OrdersInventoryError):
    """Raised when an order is not found."""
    pass


class InsufficientStockError(OrdersInventoryError):
    """Raised when there is insufficient stock for an operation."""
    pass


class DuplicateSKUError(OrdersInventoryError):
    """Raised when attempting to create a product with an existing SKU."""
    pass


class InvalidOrderStatusError(OrdersInventoryError):
    """Raised when an invalid order status transition is attempted."""
    pass


class ValidationError(OrdersInventoryError):
    """Raised when data validation fails."""
    pass

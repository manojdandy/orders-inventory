"""FastAPI exception handlers."""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Union

from ..utils.exceptions import (
    OrdersInventoryError,
    ProductNotFoundError,
    OrderNotFoundError,
    InsufficientStockError,
    DuplicateSKUError,
    InvalidOrderStatusError,
    ValidationError
)


class HTTPConflictError(HTTPException):
    """HTTP 409 Conflict error."""
    def __init__(self, detail: str):
        super().__init__(status_code=409, detail=detail)


class HTTPUnprocessableEntityError(HTTPException):
    """HTTP 422 Unprocessable Entity error."""
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)


# Exception mapping
EXCEPTION_STATUS_MAP = {
    ProductNotFoundError: 404,
    OrderNotFoundError: 404,
    DuplicateSKUError: 409,
    InsufficientStockError: 409,
    InvalidOrderStatusError: 422,
    ValidationError: 422,
}


async def orders_inventory_exception_handler(
    request: Request, 
    exc: OrdersInventoryError
) -> JSONResponse:
    """Handle custom orders_inventory exceptions."""
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    
    error_response = {
        "error": type(exc).__name__,
        "details": [
            {
                "type": type(exc).__name__,
                "message": str(exc),
                "field": None
            }
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle validation exceptions."""
    from pydantic import ValidationError as PydanticValidationError
    
    if isinstance(exc, PydanticValidationError):
        details = []
        for error in exc.errors():
            details.append({
                "type": "ValidationError",
                "message": error["msg"],
                "field": ".".join(str(loc) for loc in error["loc"])
            })
        
        error_response = {
            "error": "ValidationError",
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(
            status_code=422,
            content=error_response
        )
    
    # Generic error
    error_response = {
        "error": "InternalServerError",
        "details": [
            {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "field": None
            }
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )

"""
Global exception handling middleware.
Similar to global exception middleware in .NET Core.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception."""
    
    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Validation exception for business rule violations."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, 400, details)


class LLMServiceException(AppException):
    """LLM service related exceptions."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, 503, details)


class FileProcessingException(AppException):
    """File processing related exceptions."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, 422, details)


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup global exception handlers for the FastAPI application."""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handle custom application exceptions."""
        logger.error(f"Application exception: {exc.message}", extra={
            "path": request.url.path,
            "method": request.method,
            "details": exc.details
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.message,
                    "type": exc.__class__.__name__,
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        logger.warning(f"Validation error: {exc.errors()}", extra={
            "path": request.url.path,
            "method": request.method
        })
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "message": "Validation failed",
                    "type": "ValidationError",
                    "details": {"validation_errors": exc.errors()}
                }
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.warning(f"HTTP exception: {exc.detail}", extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "type": "HTTPException"
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {str(exc)}", extra={
            "path": request.url.path,
            "method": request.method
        }, exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "An unexpected error occurred",
                    "type": "InternalServerError"
                }
            }
        )
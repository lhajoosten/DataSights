"""
FastAPI application entry point.

This module sets up the FastAPI application with all necessary
middleware, routes, and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.exceptions import setup_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="Talk to Your Data API",
    description="Upload CSV files and generate charts from natural language questions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check endpoints for monitoring"
        },
        {
            "name": "csv", 
            "description": "CSV file upload and processing operations"
        },
        {
            "name": "chat",
            "description": "Natural language chat and chart generation"
        }
    ]
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting Talk to Your Data API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"LLM Service: {'OpenAI API' if settings.openai_api_key else 'Fallback Mode'}")
    
    # Ensure upload directory exists
    import os
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info(f"Upload directory: {settings.upload_dir}")


@app.on_event("shutdown") 
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Talk to Your Data API")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return JSONResponse({
        "message": "Talk to Your Data API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "environment": settings.environment
    })


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
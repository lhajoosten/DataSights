"""
Main API router configuration.
Similar to route configuration in .NET Web API.
"""

from fastapi import APIRouter

from app.api.endpoints import csv_routes, chat_routes, health_routes

# Create main API router
api_router = APIRouter()

# Include individual route modules
api_router.include_router(
    health_routes.router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    csv_routes.router,
    prefix="/csv",
    tags=["csv"]
)

api_router.include_router(
    chat_routes.router,
    prefix="/chat", 
    tags=["chat"]
)
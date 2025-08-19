"""
Health check endpoints.
Similar to HealthController in .NET applications.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import logging

from app.core.config import get_settings, Settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def basic_health_check():
    """Basic health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "datasights-api",
        "timestamp": "2025-08-19T14:23:06Z"
    })


@router.get("/detailed")
async def detailed_health_check(settings: Settings = Depends(get_settings)):
    """
    Detailed health check with service dependencies.
    Similar to health checks in .NET with IHealthCheck.
    """
    health_status = {
        "status": "healthy",
        "service": "datasights-api",
        "version": "1.0.0",
        "environment": settings.environment,
        "checks": {}
    }
    
    # Check LLM service availability
    llm_status = "healthy" if settings.openai_api_key else "degraded"
    health_status["checks"]["llm_service"] = {
        "status": llm_status,
        "message": "OpenAI API configured" if settings.openai_api_key else "Fallback mode (no API key)"
    }
    
    # Check file system access
    try:
        import os
        os.makedirs(settings.upload_dir, exist_ok=True)
        health_status["checks"]["file_system"] = {
            "status": "healthy",
            "message": f"Upload directory accessible: {settings.upload_dir}"
        }
    except Exception as e:
        health_status["checks"]["file_system"] = {
            "status": "unhealthy",
            "message": f"File system error: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Overall status based on checks
    if any(check["status"] == "unhealthy" for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"
    elif any(check["status"] == "degraded" for check in health_status["checks"].values()):
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503
    return JSONResponse(health_status, status_code=status_code)
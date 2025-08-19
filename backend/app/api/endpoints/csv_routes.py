"""
CSV upload and processing endpoints.
Similar to a FileController in .NET Web API.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
import logging
from typing import List

from app.services.csv_service import CSVService
from app.services.file_storage_service import FileStorageService
from app.models.csv_models import CSVPreviewResponse
from app.core.config import get_settings, Settings
from app.core.exceptions import ValidationException, FileProcessingException

logger = logging.getLogger(__name__)
router = APIRouter()


# Dependency injection - similar to .NET DI container
def get_csv_service() -> CSVService:
    """Dependency injection for CSV service."""
    return CSVService()


def get_file_storage_service() -> FileStorageService:
    """Dependency injection for file storage service."""
    return FileStorageService()


@router.post("/upload", response_model=CSVPreviewResponse)
async def upload_csv_file(
    file: UploadFile = File(..., description="CSV file to upload (max 10MB)"),
    csv_service: CSVService = Depends(get_csv_service),
    file_storage: FileStorageService = Depends(get_file_storage_service),
    settings: Settings = Depends(get_settings)
):
    """
    Upload and process CSV file.
    
    Similar to a POST action in .NET Web API with file upload handling.
    Returns preview data and file metadata for frontend display.
    """
    logger.info(f"CSV upload request: {file.filename}, size: {file.size}")
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.csv'):
            raise ValidationException(
                "Only CSV files are allowed",
                details={"filename": file.filename, "allowed_types": [".csv"]}
            )
        
        # Validate file size (client-side should catch this too)
        if file.size and file.size > settings.max_file_size_mb * 1024 * 1024:
            raise ValidationException(
                f"File size {file.size / (1024*1024):.2f}MB exceeds maximum {settings.max_file_size_mb}MB",
                details={"file_size_mb": file.size / (1024*1024), "max_size_mb": settings.max_file_size_mb}
            )
        
        # Read file content
        file_content = await file.read()
        
        # Save uploaded file
        file_id, file_path = await file_storage.save_uploaded_file(file_content, file.filename)
        
        # Process and validate CSV
        preview_response = await csv_service.validate_and_preview_csv(file_path, file.filename)
        
        # Add file_id to response for subsequent requests
        response_dict = preview_response.dict()
        response_dict["file_id"] = file_id
        
        logger.info(f"CSV upload successful: {file_id}, rows: {preview_response.rows_total}")
        
        return JSONResponse(
            content=response_dict,
            status_code=201,
            headers={"Location": f"/api/v1/csv/{file_id}"}
        )
        
    except (ValidationException, FileProcessingException) as e:
        logger.warning(f"CSV upload validation failed: {e.message}")
        raise HTTPException(status_code=e.status_code, detail={
            "error": e.message,
            "type": e.__class__.__name__,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error in CSV upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": "Internal server error during file upload",
            "type": "InternalServerError"
        })


@router.get("/{file_id}/metadata")
async def get_csv_metadata(
    file_id: str,
    csv_service: CSVService = Depends(get_csv_service),
    file_storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Get CSV metadata by file ID.
    
    Similar to a GET action in .NET Web API for resource retrieval.
    Used by frontend for displaying file information and LLM context.
    """
    logger.info(f"CSV metadata request: {file_id}")
    
    try:
        # Get file path
        file_path = await file_storage.get_file_path(file_id)
        
        # Get metadata
        metadata = await csv_service.get_csv_metadata(file_path, file_id)
        
        return JSONResponse(metadata.dict())
        
    except FileProcessingException as e:
        logger.warning(f"CSV metadata not found: {file_id}")
        raise HTTPException(status_code=404, detail={
            "error": f"CSV file not found: {file_id}",
            "type": "NotFound"
        })
    except Exception as e:
        logger.error(f"Error getting CSV metadata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": "Internal server error retrieving metadata",
            "type": "InternalServerError"
        })


@router.delete("/{file_id}")
async def delete_csv_file(
    file_id: str,
    file_storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Delete uploaded CSV file.
    
    Similar to a DELETE action in .NET Web API.
    Cleans up temporary files when user is done with analysis.
    """
    logger.info(f"CSV delete request: {file_id}")
    
    try:
        await file_storage.delete_file(file_id)
        
        return JSONResponse({
            "message": f"File {file_id} deleted successfully",
            "file_id": file_id
        })
        
    except FileProcessingException:
        # File not found - return success anyway (idempotent delete)
        return JSONResponse({
            "message": f"File {file_id} not found (may already be deleted)",
            "file_id": file_id
        })
    except Exception as e:
        logger.error(f"Error deleting CSV file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": "Internal server error during file deletion",
            "type": "InternalServerError"
        })


@router.post("/cleanup")
async def cleanup_old_files(
    max_age_hours: int = 24,
    file_storage: FileStorageService = Depends(get_file_storage_service)
):
    """
    Cleanup old uploaded files.
    
    Similar to a maintenance action in .NET Web API.
    Can be called by background services or admin endpoints.
    """
    logger.info(f"File cleanup request: max_age_hours={max_age_hours}")
    
    try:
        cleaned_count = await file_storage.cleanup_old_files(max_age_hours)
        
        return JSONResponse({
            "message": f"Cleanup completed: {cleaned_count} files removed",
            "files_cleaned": cleaned_count,
            "max_age_hours": max_age_hours
        })
        
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": "Internal server error during cleanup",
            "type": "InternalServerError"
        })
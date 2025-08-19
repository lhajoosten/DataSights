"""
File storage service for handling uploaded CSV files.
Similar to a storage abstraction in .NET for file operations.
"""

import os
import uuid
import aiofiles
import hashlib
from typing import BinaryIO, Tuple
from pathlib import Path
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.exceptions import FileProcessingException


class FileStorageService:
    """Service for handling file storage operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.upload_dir)
        self._ensure_upload_directory()
    
    def _ensure_upload_directory(self) -> None:
        """Ensure upload directory exists."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(self, file_content: bytes, original_filename: str) -> Tuple[str, str]:
        """
        Save uploaded file and return file_id and file_path.
        
        Args:
            file_content: Raw file bytes
            original_filename: Original filename from upload
            
        Returns:
            Tuple of (file_id, file_path)
            
        Raises:
            FileProcessingException: If file cannot be saved
        """
        try:
            # Generate unique file ID
            file_id = self._generate_file_id(original_filename)
            
            # Create safe filename
            safe_filename = self._create_safe_filename(file_id, original_filename)
            file_path = self.upload_dir / safe_filename
            
            # Save file asynchronously
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            return file_id, str(file_path)
            
        except Exception as e:
            raise FileProcessingException(
                f"Failed to save uploaded file: {str(e)}",
                details={"original_filename": original_filename}
            )
    
    async def get_file_path(self, file_id: str) -> str:
        """
        Get file path by file ID.
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            Full file path
            
        Raises:
            FileProcessingException: If file not found
        """
        # Find file with matching file_id prefix
        for file_path in self.upload_dir.glob(f"{file_id}_*"):
            if file_path.is_file():
                return str(file_path)
        
        raise FileProcessingException(
            f"File with ID {file_id} not found",
            details={"file_id": file_id}
        )
    
    async def delete_file(self, file_id: str) -> None:
        """
        Delete file by file ID.
        
        Args:
            file_id: Unique file identifier
        """
        try:
            file_path = await self.get_file_path(file_id)
            os.remove(file_path)
        except FileProcessingException:
            # File doesn't exist, which is fine for delete operation
            pass
        except Exception as e:
            raise FileProcessingException(
                f"Failed to delete file: {str(e)}",
                details={"file_id": file_id}
            )
    
    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up files older than specified hours.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        
        try:
            for file_path in self.upload_dir.glob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    os.remove(file_path)
                    cleaned_count += 1
        except Exception as e:
            # Log but don't fail - cleanup is best effort
            pass
        
        return cleaned_count
    
    def _generate_file_id(self, filename: str) -> str:
        """Generate unique file ID based on timestamp and filename."""
        timestamp = datetime.now(timezone.utc).isoformat()
        content = f"{timestamp}_{filename}_{uuid.uuid4()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _create_safe_filename(self, file_id: str, original_filename: str) -> str:
        """Create safe filename for storage."""
        # Extract extension safely
        extension = Path(original_filename).suffix.lower()
        if extension not in ['.csv']:
            extension = '.csv'
        
        return f"{file_id}_{original_filename.replace(' ', '_')}{extension}"
    
    def get_file_size_mb(self, file_path: str) -> float:
        """Get file size in megabytes."""
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
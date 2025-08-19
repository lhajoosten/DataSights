"""
File handling utility functions.
Similar to file utilities in .NET applications.
"""

import os
import hashlib
import aiofiles
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timezone


async def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure directory exists, create if necessary.
    Similar to Directory.CreateDirectory in .NET.
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)


def get_file_hash(file_content: bytes) -> str:
    """
    Generate MD5 hash of file content.
    Similar to hash generation in .NET cryptography.
    """
    return hashlib.md5(file_content).hexdigest()


def get_safe_filename(original_filename: str, file_id: str) -> str:
    """
    Generate safe filename for storage.
    Similar to safe filename generation in .NET file handling.
    """
    # Extract extension
    path = Path(original_filename)
    extension = path.suffix.lower()
    
    # Ensure CSV extension
    if extension not in ['.csv']:
        extension = '.csv'
    
    # Create safe base name
    safe_name = "".join(c for c in path.stem if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    
    # Limit length
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
    
    return f"{file_id}_{safe_name}{extension}"


async def cleanup_temp_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Clean up temporary files older than specified age.
    Similar to cleanup utilities in .NET applications.
    """
    cleaned_count = 0
    cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
    
    try:
        directory_path = Path(directory)
        if not directory_path.exists():
            return 0
        
        for file_path in directory_path.iterdir():
            if file_path.is_file():
                try:
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
                except (OSError, PermissionError):
                    # Skip files that can't be deleted
                    continue
    
    except Exception:
        # Best effort cleanup - don't fail if there are issues
        pass
    
    return cleaned_count


def get_file_info(file_path: str) -> Optional[dict]:
    """
    Get file information including size, modification time, etc.
    Similar to FileInfo in .NET System.IO.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        
        stat = path.stat()
        return {
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "created_time": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
            "modified_time": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "extension": path.suffix.lower(),
            "filename": path.name
        }
    
    except Exception:
        return None
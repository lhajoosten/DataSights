"""
Validation utility functions.
Similar to validation helpers in .NET with FluentValidation patterns.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate file extension against allowed list.
    Similar to file validation in .NET applications.
    """
    if not filename:
        return False
    
    file_ext = filename.lower().split('.')[-1]
    return f".{file_ext}" in [ext.lower() for ext in allowed_extensions]


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    Similar to input sanitization in .NET applications.
    """
    if not filename:
        return "unnamed_file"
    
    # Remove or replace dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove extra spaces and limit length
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    
    # Limit filename length
    if len(sanitized) > 100:
        name_part = sanitized[:95]
        ext_part = sanitized[sanitized.rfind('.'):]
        sanitized = name_part + ext_part
    
    return sanitized


def validate_csv_content(content: bytes, max_size_mb: int = 10) -> Dict[str, Any]:
    """
    Validate CSV content before processing.
    Similar to content validation in .NET applications.
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "size_mb": len(content) / (1024 * 1024)
    }
    
    # Check file size
    if validation_result["size_mb"] > max_size_mb:
        validation_result["is_valid"] = False
        validation_result["errors"].append(f"File size {validation_result['size_mb']:.2f}MB exceeds maximum {max_size_mb}MB")
    
    # Check if content looks like CSV
    try:
        content_str = content.decode('utf-8', errors='ignore')
        
        # Basic CSV format check
        lines = content_str.split('\n')[:10]  # Check first 10 lines
        
        if len(lines) < 2:
            validation_result["warnings"].append("File appears to have very few rows")
        
        # Check for consistent delimiter
        delimiters = [',', ';', '\t']
        delimiter_counts = {}
        
        for delimiter in delimiters:
            count = sum(line.count(delimiter) for line in lines[:3])
            if count > 0:
                delimiter_counts[delimiter] = count
        
        if not delimiter_counts:
            validation_result["warnings"].append("No clear CSV delimiter found")
        
    except Exception as e:
        validation_result["warnings"].append(f"Content validation warning: {str(e)}")
    
    return validation_result


def validate_column_name(column_name: str) -> bool:
    """
    Validate column name for chart generation.
    Similar to property name validation in .NET.
    """
    if not column_name or not isinstance(column_name, str):
        return False
    
    # Check for reasonable length
    if len(column_name.strip()) == 0 or len(column_name) > 100:
        return False
    
    return True


def validate_chart_data_types(df: pd.DataFrame, chart_type: str, x_col: str, y_col: str) -> Dict[str, Any]:
    """
    Validate data types are appropriate for chart type.
    Similar to business rule validation in .NET domain services.
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "suggestions": []
    }
    
    if x_col not in df.columns:
        validation_result["is_valid"] = False
        validation_result["errors"].append(f"X-axis column '{x_col}' not found")
        return validation_result
    
    if y_col not in df.columns:
        validation_result["is_valid"] = False  
        validation_result["errors"].append(f"Y-axis column '{y_col}' not found")
        return validation_result
    
    x_dtype = str(df[x_col].dtype)
    y_dtype = str(df[y_col].dtype)
    
    # Chart type specific validations
    if chart_type == "scatter":
        if not pd.api.types.is_numeric_dtype(df[x_col]):
            validation_result["suggestions"].append(f"Scatter plots work best with numeric X-axis. {x_col} appears to be {x_dtype}")
        
        if not pd.api.types.is_numeric_dtype(df[y_col]):
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Scatter plots require numeric Y-axis. {y_col} is {y_dtype}")
    
    elif chart_type == "pie":
        if pd.api.types.is_datetime64_any_dtype(df[x_col]):
            validation_result["suggestions"].append("Pie charts with datetime categories may have too many slices")
        
        if not pd.api.types.is_numeric_dtype(df[y_col]):
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Pie charts require numeric values. {y_col} is {y_dtype}")
    
    return validation_result
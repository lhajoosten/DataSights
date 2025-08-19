"""
CSV-related data models and DTOs.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CSVPreviewResponse(BaseModel):
    """Response model for CSV preview data."""

    filename: str = Field(..., description="Original filename")
    rows_total: int = Field(..., description="Total number of rows in CSV")
    columns_total: int = Field(..., description="Total number of columns")
    preview_rows: List[Dict[str, Any]] = Field(..., description="First 20 rows of data")
    column_info: Dict[str, str] = Field(
        ..., description="Column names and inferred types"
    )
    file_size_mb: float = Field(..., description="File size in megabytes")

    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "sales_data.csv",
                "rows_total": 1000,
                "columns_total": 5,
                "preview_rows": [
                    {"date": "2024-01-01", "region": "North", "sales": 100.50},
                    {"date": "2024-01-02", "region": "South", "sales": 200.75},
                ],
                "column_info": {
                    "date": "datetime",
                    "region": "string",
                    "sales": "float",
                },
                "file_size_mb": 0.5,
            }
        }
    }


class CSVValidationResult(BaseModel):
    """Result of CSV validation process."""

    is_valid: bool = Field(..., description="Whether CSV is valid")
    error_message: Optional[str] = Field(None, description="Error message if invalid")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")

    @classmethod
    def success(cls, warnings: List[str] = None) -> "CSVValidationResult": # type: ignore
        """Create a successful validation result."""
        return cls(is_valid=True, warnings=warnings or []) # type: ignore

    @classmethod
    def failure(cls, error_message: str) -> "CSVValidationResult":
        """Create a failed validation result."""
        return cls(is_valid=False, error_message=error_message)


class CSVMetadata(BaseModel):
    """Metadata about uploaded CSV file."""

    filename: str
    file_id: str = Field(..., description="Unique identifier for uploaded file")
    columns: List[str] = Field(..., description="Column names")
    column_types: Dict[str, str] = Field(..., description="Inferred column types")
    row_count: int
    file_size_bytes: int
    upload_timestamp: str = Field(..., description="ISO timestamp of upload")

    def get_numeric_columns(self) -> List[str]:
        """Get list of numeric columns for chart generation."""
        numeric_types = {"int64", "float64", "int32", "float32", "number"}
        return [
            col for col, dtype in self.column_types.items() if dtype in numeric_types
        ]

    def get_categorical_columns(self) -> List[str]:
        """Get list of categorical columns for grouping."""
        categorical_types = {"object", "string", "category"}
        return [
            col
            for col, dtype in self.column_types.items()
            if dtype in categorical_types
        ]

    def get_datetime_columns(self) -> List[str]:
        """Get list of datetime columns for time-based analysis."""
        datetime_types = {"datetime64[ns]", "datetime", "date"}
        return [
            col for col, dtype in self.column_types.items() if dtype in datetime_types
        ]

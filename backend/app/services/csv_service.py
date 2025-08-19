"""
CSV processing service for file validation and data analysis.
Similar to a domain service in Clean Architecture.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from pathlib import Path
import logging
import warnings

from app.models.csv_models import CSVPreviewResponse, CSVValidationResult, CSVMetadata
from app.core.exceptions import FileProcessingException, ValidationException
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Suppress pandas warnings for date parsing
warnings.filterwarnings('ignore', message='Could not infer format')

class CSVService:
    """Service for CSV file processing and validation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.max_preview_rows = 20
        self.max_columns = 200
    
    async def validate_and_preview_csv(self, file_path: str, filename: str) -> CSVPreviewResponse:
        """
        Validate CSV file and generate preview data.
        
        Args:
            file_path: Path to the uploaded CSV file
            filename: Original filename
            
        Returns:
            CSVPreviewResponse with validation results and preview data
            
        Raises:
            FileProcessingException: If file cannot be processed
            ValidationException: If CSV validation fails
        """
        try:
            # Validate file size
            file_size_mb = self._get_file_size_mb(file_path)
            if file_size_mb > self.settings.max_file_size_mb:
                raise ValidationException(
                    f"File size {file_size_mb:.2f}MB exceeds maximum allowed size of {self.settings.max_file_size_mb}MB"
                )
            
            # Read and validate CSV
            df = await self._read_csv_safely(file_path)
            validation_result = self._validate_csv_structure(df)
            
            if not validation_result.is_valid:
                raise ValidationException(validation_result.error_message)
            
            # Generate preview data
            preview_data = self._generate_preview_data(df)
            column_info = self._analyze_column_types(df)
            
            return CSVPreviewResponse(
                filename=filename,
                rows_total=len(df),
                columns_total=len(df.columns),
                preview_rows=preview_data,
                column_info=column_info,
                file_size_mb=file_size_mb
            )
            
        except (ValidationException, FileProcessingException):
            # Re-raise known exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing CSV: {str(e)}", exc_info=True)
            raise FileProcessingException(
                f"Failed to process CSV file: {str(e)}",
                details={"filename": filename, "file_path": file_path}
            )
    
    async def get_csv_metadata(self, file_path: str, file_id: str) -> CSVMetadata:
        """
        Get detailed metadata about CSV file for LLM context.
        
        Args:
            file_path: Path to CSV file
            file_id: Unique file identifier
            
        Returns:
            CSVMetadata object with detailed file information
        """
        try:
            df = await self._read_csv_safely(file_path)
            column_info = self._analyze_column_types(df)
            
            return CSVMetadata(
                filename=Path(file_path).name,
                file_id=file_id,
                columns=list(df.columns),
                column_types=column_info,
                row_count=len(df),
                file_size_bytes=Path(file_path).stat().st_size,
                upload_timestamp=pd.Timestamp.now(tz='UTC').isoformat()
            )
            
        except Exception as e:
            raise FileProcessingException(
                f"Failed to get CSV metadata: {str(e)}",
                details={"file_id": file_id, "file_path": file_path}
            )
    
    async def load_dataframe(self, file_path: str) -> pd.DataFrame:
        """
        Load CSV file as pandas DataFrame for chart generation.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Pandas DataFrame with processed data
        """
        try:
            df = await self._read_csv_safely(file_path)
            return self._clean_dataframe(df)
            
        except Exception as e:
            raise FileProcessingException(
                f"Failed to load DataFrame: {str(e)}",
                details={"file_path": file_path}
            )
    
    async def _read_csv_safely(self, file_path: str) -> pd.DataFrame:
        """
        Safely read CSV file with robust parsing options.
        Similar to defensive programming practices in .NET.
        """
        try:
            # Try reading with different encodings if needed
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(
                        file_path,
                        encoding=encoding,
                        low_memory=False,
                        dtype=str,  # Read everything as string initially
                        na_values=['', 'NULL', 'null', 'NA', 'N/A', 'nan'],
                        keep_default_na=True
                    )
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise FileProcessingException("Could not decode file with supported encodings")
            
            if df.empty:
                raise ValidationException("CSV file is empty")
                
            return df
            
        except pd.errors.EmptyDataError:
            raise ValidationException("CSV file contains no data")
        except pd.errors.ParserError as e:
            raise ValidationException(f"CSV parsing error: {str(e)}")
        except Exception as e:
            raise FileProcessingException(f"Failed to read CSV file: {str(e)}")
    
    def _validate_csv_structure(self, df: pd.DataFrame) -> CSVValidationResult:
        """
        Validate CSV structure and content.
        Similar to validation services in .NET with FluentValidation.
        """
        warnings = []
        
        # Check column count
        if len(df.columns) > self.max_columns:
            return CSVValidationResult.failure(
                f"Too many columns ({len(df.columns)}). Maximum allowed: {self.max_columns}"
            )
        
        # Check for duplicate column names
        duplicate_columns = df.columns[df.columns.duplicated()].tolist()
        if duplicate_columns:
            return CSVValidationResult.failure(
                f"Duplicate column names found: {duplicate_columns}"
            )
        
        # Check for empty column names
        empty_columns = [i for i, col in enumerate(df.columns) if pd.isna(col) or str(col).strip() == '']
        if empty_columns:
            return CSVValidationResult.failure(
                f"Empty column names found at positions: {empty_columns}"
            )
        
        # Warnings for potential issues
        if len(df.columns) == 1:
            warnings.append("CSV has only one column. Check if delimiter is correct.")
        
        if df.isnull().sum().sum() > (len(df) * len(df.columns) * 0.5):
            warnings.append("CSV has many missing values (>50%). Verify data quality.")
        
        return CSVValidationResult.success(warnings)
    
    def _generate_preview_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate preview data for frontend display."""
        preview_df = df.head(self.max_preview_rows).copy()
        
        # Convert to appropriate types for JSON serialization
        for col in preview_df.columns:
            preview_df[col] = preview_df[col].astype(str).replace('nan', None)
        
        return preview_df.to_dict('records')
    
    def _analyze_column_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Analyze and infer column data types.
        Similar to type inference in strongly-typed languages.
        """
        column_types = {}
        
        for col in df.columns:
            series = df[col].dropna()
            
            if len(series) == 0:
                column_types[col] = 'unknown'
                continue
            
            # Try to infer type
            col_type = self._infer_column_type(series)
            column_types[col] = col_type
        
        return column_types
    
    def _infer_column_type(self, series: pd.Series) -> str:
        """Infer the most appropriate data type for a column."""
        # Skip empty series
        if len(series) == 0:
            return 'unknown'
        
        # Take a sample for type inference (avoid processing entire column)
        sample_size = min(100, len(series))
        sample = series.head(sample_size).dropna()
        
        if len(sample) == 0:
            return 'unknown'
        
        # Try datetime first (with warning suppression)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Try common date formats first
                for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        pd.to_datetime(sample, format=date_format, errors='raise')
                        return 'datetime'
                    except (ValueError, TypeError):
                        continue
                
                # Try automatic inference as last resort
                parsed_dates = pd.to_datetime(sample, errors='coerce', infer_datetime_format=True)
                if parsed_dates.notna().sum() > len(sample) * 0.7:  # 70% success rate
                    return 'datetime'
        except Exception:
            pass
        
        # Try numeric
        try:
            numeric_series = pd.to_numeric(sample, errors='raise')
            if numeric_series.dtype in ['int64', 'int32']:
                return 'integer'
            else:
                return 'float'
        except (ValueError, TypeError):
            pass
        
        # Try boolean
        unique_values = set(str(val).lower() for val in sample.unique())
        boolean_values = {'true', 'false', '1', '0', 'yes', 'no', 'y', 'n'}
        if unique_values.issubset(boolean_values) and len(unique_values) <= 2:
            return 'boolean'
        
        # Check if categorical (limited unique values)
        unique_count = len(sample.unique())
        if unique_count < len(sample) * 0.5 and unique_count < 50:
            return 'category'
        
        # Default to string
        return 'string'
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare DataFrame for analysis.
        Similar to data sanitization in .NET applications.
        """
        cleaned_df = df.copy()
        
        # Clean column names
        cleaned_df.columns = [self._clean_column_name(col) for col in cleaned_df.columns]
        
        # Convert columns to appropriate types with better error handling
        for col in cleaned_df.columns:
            try:
                cleaned_df[col] = self._convert_column_type_safe(cleaned_df[col])
            except Exception as e:
                logger.warning(f"Could not convert column {col}: {str(e)}")
                # Keep original column if conversion fails
        
        return cleaned_df
    
    def _convert_column_type_safe(self, series: pd.Series) -> pd.Series:
        """Convert series to most appropriate data type with error handling."""
        # Skip if series is empty
        if len(series) == 0:
            return series
        
        # Try datetime conversion with better format handling
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Try common formats first
                for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        converted = pd.to_datetime(series, format=date_format, errors='raise')
                        return converted
                    except (ValueError, TypeError):
                        continue
                
                # Try automatic inference
                converted = pd.to_datetime(series, errors='coerce', infer_datetime_format=True)
                if converted.notna().sum() > len(series) * 0.7:  # 70% success rate
                    return converted
        except Exception:
            pass
        
        # Try numeric conversion
        try:
            return pd.to_numeric(series, errors='raise')
        except (ValueError, TypeError):
            pass
        
        # Keep as string/object
        return series
    
    def _clean_column_name(self, col_name: str) -> str:
        """Clean column name for consistent usage."""
        # Remove extra whitespace and convert to lowercase
        clean_name = str(col_name).strip().lower()
        # Replace spaces and special characters with underscores
        clean_name = ''.join(c if c.isalnum() else '_' for c in clean_name)
        # Remove consecutive underscores
        while '__' in clean_name:
            clean_name = clean_name.replace('__', '_')
        # Remove leading/trailing underscores
        clean_name = clean_name.strip('_')
        
        return clean_name if clean_name else 'unnamed_column'
    
    def _convert_column_type(self, series: pd.Series) -> pd.Series:
        """Convert series to most appropriate data type."""
        # Try datetime conversion
        try:
            return pd.to_datetime(series, errors='raise')
        except:
            pass
        
        # Try numeric conversion
        try:
            return pd.to_numeric(series, errors='raise')
        except:
            pass
        
        # Keep as string/object
        return series
    
    def _get_file_size_mb(self, file_path: str) -> float:
        """Get file size in megabytes."""
        size_bytes = Path(file_path).stat().st_size
        return size_bytes / (1024 * 1024)
"""
Enhanced chart generation service with calculated field support.
Similar to a data transformation service in .NET applications.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
import warnings

from app.models.chart_models import ChartSpec, ChartData, ChartValidationResult, FilterSpec, CalculationSpec
from app.models.csv_models import CSVMetadata
from app.core.exceptions import ValidationException, FileProcessingException

logger = logging.getLogger(__name__)

# Suppress pandas warnings
warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)


class ChartService:
    """
    Enhanced service for generating chart data with calculated field support.
    Handles data transformation, aggregation, and chart-specific processing.
    """
    
    def __init__(self):
        self.max_data_points = 1000  # Limit for performance
        self.max_categories = 50     # Limit for readability
    
    async def generate_chart_data(
        self, 
        chart_spec: ChartSpec, 
        dataframe: pd.DataFrame,
        csv_metadata: CSVMetadata
    ) -> ChartData:
        """
        Generate chart data with support for calculated fields and complex operations.
        
        Args:
            chart_spec: Chart specification from LLM
            dataframe: Source DataFrame
            csv_metadata: CSV metadata for validation
            
        Returns:
            ChartData ready for frontend visualization
            
        Raises:
            ValidationException: If chart spec is invalid for the data
        """
        try:
            # Create working copy
            processed_df = dataframe.copy()
            transformations = []
            
            # Step 1: Apply calculated fields first
            if chart_spec.calculation:
                processed_df, calc_transformations = await self._apply_calculated_field(
                    processed_df, chart_spec.calculation
                )
                transformations.extend(calc_transformations)
            
            # Step 2: Handle time-based grouping (extract month/year from dates)
            processed_df, time_transformations = await self._handle_time_grouping(
                processed_df, chart_spec
            )
            transformations.extend(time_transformations)
            
            # Step 3: Validate chart specification against processed data
            validation_result = await self._validate_enhanced_chart_spec(chart_spec, processed_df, csv_metadata)
            if not validation_result.is_valid:
                raise ValidationException(
                    validation_result.error_message,
                    details={"suggestions": validation_result.suggestions}
                )
            
            # Step 4: Apply filters
            if chart_spec.filters:
                processed_df, filter_transformations = self._apply_filters(processed_df, chart_spec.filters)
                transformations.extend(filter_transformations)
            
            # Step 5: Apply grouping and aggregation
            if chart_spec.group_by or chart_spec.aggregation != "none":
                processed_df, agg_transformations = await self._apply_enhanced_aggregation(
                    processed_df, chart_spec
                )
                transformations.extend(agg_transformations)
            
            # Step 6: Limit data points for performance
            if len(processed_df) > self.max_data_points:
                processed_df = processed_df.head(self.max_data_points)
                transformations.append(f"Limited to {self.max_data_points} data points for performance")
            
            # Step 7: Sort data for better visualization
            if chart_spec.x and chart_spec.x in processed_df.columns:
                try:
                    processed_df = processed_df.sort_values(chart_spec.x)
                    transformations.append(f"Sorted by {chart_spec.x}")
                except Exception:
                    # If sorting fails, continue without sorting
                    pass
            
            # Step 8: Generate chart-specific data
            chart_data = await self._generate_chart_specific_data(chart_spec, processed_df)
            
            # Step 9: Calculate summary statistics
            summary_stats = self._calculate_summary_stats(processed_df, chart_spec)
            
            return ChartData(
                chart_spec=chart_spec,
                data=chart_data,
                summary_stats=summary_stats,
                data_transformations=transformations
            )
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Chart generation error: {str(e)}", exc_info=True)
            raise FileProcessingException(
                f"Failed to generate chart data: {str(e)}",
                details={"chart_type": chart_spec.chart_type}
            )
    
    async def _apply_calculated_field(
        self, 
        df: pd.DataFrame, 
        calculation: CalculationSpec
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Apply calculated field to DataFrame using safe operations."""
        transformations = []
        
        try:
            formula = calculation.formula
            field_name = calculation.field_name
            
            logger.info(f"Applying calculation: {field_name} = {formula}")
            
            # Extract column names from formula
            column_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
            referenced_columns = re.findall(column_pattern, formula)
            
            # Filter to only actual column names
            operators_keywords = {'and', 'or', 'not', 'if', 'else', 'true', 'false', 'sum', 'mean', 'min', 'max'}
            actual_columns = [col for col in referenced_columns 
                            if col in df.columns and col.lower() not in operators_keywords]
            
            # Validate all referenced columns exist
            missing_columns = [col for col in actual_columns if col not in df.columns]
            if missing_columns:
                raise ValidationException(f"Columns not found for calculation: {missing_columns}")
            
            # Apply safe calculation
            result_series = self._safe_calculate(df, formula, actual_columns)
            df[field_name] = result_series
            
            transformations.append(f"Calculated {field_name} = {formula}")
            transformations.append(f"Description: {calculation.description}")
            
            logger.info(f"Successfully calculated {field_name}, sample values: {result_series.head(3).tolist()}")
            
            return df, transformations
            
        except Exception as e:
            logger.error(f"Calculated field error: {str(e)}")
            raise ValidationException(
                f"Failed to calculate {calculation.field_name}: {str(e)}",
                details={"formula": calculation.formula, "available_columns": list(df.columns)}
            )
    
    def _safe_calculate(self, df: pd.DataFrame, formula: str, columns: List[str]) -> pd.Series:
        """Safely perform calculations on DataFrame columns."""
        try:
            # Convert columns to numeric where possible
            numeric_df = df.copy()
            for col in columns:
                numeric_df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Create a safe evaluation environment
            safe_dict = {
                '__builtins__': {},
                'abs': abs,
                'max': max,
                'min': min,
                'sum': sum,
                'round': round,
                'pow': pow,
                'sqrt': lambda x: np.sqrt(x),
                'log': lambda x: np.log(x),
                'exp': lambda x: np.exp(x),
                'np': np,
                'pd': pd,
            }
            
            # Add column data to safe environment
            for col in columns:
                safe_dict[col] = numeric_df[col]
            
            # Check for dangerous operations
            dangerous_patterns = ['import', 'exec', 'eval', '__', 'open', 'file', 'input', 'raw_input']
            if any(pattern in formula.lower() for pattern in dangerous_patterns):
                raise ValueError("Unsafe operation detected in formula")
            
            # Evaluate the formula
            result = eval(formula, safe_dict, {})
            
            # Ensure result is a pandas Series
            if isinstance(result, (int, float)):
                # Scalar result - broadcast to all rows
                result = pd.Series([result] * len(df))
            elif isinstance(result, np.ndarray):
                result = pd.Series(result)
            elif not isinstance(result, pd.Series):
                result = pd.Series(result)
            
            # Handle any NaN values
            result = result.fillna(0)
            
            return result
            
        except Exception as e:
            logger.error(f"Formula evaluation failed: {formula}, error: {str(e)}")
            raise ValueError(f"Formula evaluation failed: {str(e)}")
    
    async def _handle_time_grouping(
        self, 
        df: pd.DataFrame, 
        chart_spec: ChartSpec
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Handle time-based grouping by extracting periods from date columns."""
        transformations = []
        
        try:
            # Check if x-axis requests time-based grouping
            if chart_spec.x and any(period in chart_spec.x.lower() 
                                  for period in ['month', 'year', 'quarter', 'week']):
                
                # Find date column
                date_col = self._find_date_column(df)
                if date_col:
                    date_series = pd.to_datetime(df[date_col], errors='coerce')
                    
                    if 'month' in chart_spec.x.lower():
                        df['month'] = date_series.dt.strftime('%Y-%m')
                        transformations.append(f"Extracted month from {date_col}")
                    elif 'year' in chart_spec.x.lower():
                        df['year'] = date_series.dt.year
                        transformations.append(f"Extracted year from {date_col}")
                    elif 'quarter' in chart_spec.x.lower():
                        df['quarter'] = date_series.dt.to_period('Q').astype(str)
                        transformations.append(f"Extracted quarter from {date_col}")
                    elif 'week' in chart_spec.x.lower():
                        df['week'] = date_series.dt.strftime('%Y-W%U')
                        transformations.append(f"Extracted week from {date_col}")
            
            return df, transformations
            
        except Exception as e:
            logger.warning(f"Time grouping failed: {str(e)}")
            return df, transformations
    
    def _find_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the first date column in the DataFrame."""
        for col in df.columns:
            try:
                # Try to convert a sample to datetime
                sample = df[col].dropna().head(10)
                if len(sample) == 0:
                    continue
                    
                pd.to_datetime(sample, errors='raise')
                return col
            except:
                continue
        return None
    
    async def _validate_enhanced_chart_spec(
        self, 
        chart_spec: ChartSpec, 
        df: pd.DataFrame,
        csv_metadata: CSVMetadata
    ) -> ChartValidationResult:
        """Validate chart specification against processed DataFrame."""
        suggestions = []
        
        # Get available columns (including calculated ones)
        available_columns = set(df.columns)
        
        # Check x-axis column
        if chart_spec.x and chart_spec.x not in available_columns:
            return ChartValidationResult.failure(
                f"X-axis column '{chart_spec.x}' not found in data",
                suggestions=[f"Available columns: {', '.join(available_columns)}"]
            )
        
        # Check y-axis column
        if chart_spec.y and chart_spec.y not in available_columns:
            return ChartValidationResult.failure(
                f"Y-axis column '{chart_spec.y}' not found in data",
                suggestions=[f"Available columns: {', '.join(available_columns)}"]
            )
        
        # Check group_by columns
        if chart_spec.group_by:
            invalid_groups = [col for col in chart_spec.group_by if col not in available_columns]
            if invalid_groups:
                return ChartValidationResult.failure(
                    f"Group by columns not found: {invalid_groups}",
                    suggestions=[f"Available columns: {', '.join(available_columns)}"]
                )
        
        # Validate chart type requirements with processed data
        if chart_spec.chart_type == "scatter":
            if chart_spec.x and not pd.api.types.is_numeric_dtype(df[chart_spec.x]):
                suggestions.append("Consider using aggregation or different chart type for non-numeric X-axis")
            if chart_spec.y and not pd.api.types.is_numeric_dtype(df[chart_spec.y]):
                return ChartValidationResult.failure(
                    f"Scatter plot Y-axis '{chart_spec.y}' must be numeric"
                )
        
        elif chart_spec.chart_type == "pie":
            if chart_spec.y and not pd.api.types.is_numeric_dtype(df[chart_spec.y]):
                return ChartValidationResult.failure(
                    f"Pie chart values '{chart_spec.y}' must be numeric"
                )
        
        return ChartValidationResult.success()
    
    async def _apply_enhanced_aggregation(
        self, 
        df: pd.DataFrame, 
        chart_spec: ChartSpec
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Apply enhanced aggregation with multi-dimensional grouping support."""
        transformations = []
        
        if chart_spec.aggregation == "none" and not chart_spec.group_by:
            return df, transformations
        
        # Determine grouping columns
        group_cols = []
        if chart_spec.group_by:
            group_cols.extend(chart_spec.group_by)
        if chart_spec.x and chart_spec.x not in group_cols:
            group_cols.append(chart_spec.x)
        
        # Remove None values and ensure columns exist
        group_cols = [col for col in group_cols if col and col in df.columns]
        
        if not group_cols:
            return df, transformations
        
        try:
            if chart_spec.aggregation == "count":
                # Count aggregation
                agg_df = df.groupby(group_cols).size().reset_index(name='count')
                # Update chart spec to use count column
                chart_spec.y = 'count'
                transformations.append(f"Grouped by {group_cols} and counted rows")
                
            else:
                # Numeric aggregation
                if not chart_spec.y or chart_spec.y not in df.columns:
                    return df, transformations
                
                agg_func = {
                    "sum": "sum",
                    "mean": "mean", 
                    "min": "min",
                    "max": "max"
                }.get(chart_spec.aggregation, "sum")
                
                # Convert to numeric for aggregation
                df[chart_spec.y] = pd.to_numeric(df[chart_spec.y], errors='coerce')
                
                # Handle multi-dimensional grouping
                agg_df = df.groupby(group_cols)[chart_spec.y].agg(agg_func).reset_index()
                transformations.append(f"Grouped by {group_cols} and applied {agg_func} to {chart_spec.y}")
            
            return agg_df, transformations
            
        except Exception as e:
            logger.warning(f"Aggregation failed: {str(e)}")
            return df, transformations
    
    def _apply_filters(
        self, 
        df: pd.DataFrame, 
        filters: List[FilterSpec]
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Apply filters to DataFrame."""
        filtered_df = df.copy()
        transformations = []
        
        for filter_spec in filters:
            col = filter_spec.column
            op = filter_spec.operator
            value = filter_spec.value
            
            if col not in filtered_df.columns:
                continue
            
            try:
                if op == "==":
                    mask = filtered_df[col] == value
                elif op == "!=":
                    mask = filtered_df[col] != value
                elif op == ">":
                    mask = pd.to_numeric(filtered_df[col], errors='coerce') > float(value)
                elif op == ">=":
                    mask = pd.to_numeric(filtered_df[col], errors='coerce') >= float(value)
                elif op == "<":
                    mask = pd.to_numeric(filtered_df[col], errors='coerce') < float(value)
                elif op == "<=":
                    mask = pd.to_numeric(filtered_df[col], errors='coerce') <= float(value)
                elif op == "in":
                    mask = filtered_df[col].isin(value)
                elif op == "not_in":
                    mask = ~filtered_df[col].isin(value)
                else:
                    continue
                
                filtered_df = filtered_df[mask]
                transformations.append(f"Filtered {col} {op} {value}")
                
            except Exception as e:
                logger.warning(f"Failed to apply filter {col} {op} {value}: {str(e)}")
                continue
        
        return filtered_df, transformations
    
    async def _generate_chart_specific_data(
        self, 
        chart_spec: ChartSpec, 
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Generate chart-specific data format."""
        if chart_spec.chart_type == "pie":
            return self._format_pie_chart_data(chart_spec, df)
        else:
            return self._format_standard_chart_data(chart_spec, df)
    
    def _format_pie_chart_data(
        self, 
        chart_spec: ChartSpec, 
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Format data for pie charts."""
        if not chart_spec.x or not chart_spec.y:
            return []
        
        # Limit categories for readability
        if len(df) > self.max_categories:
            df_top = df.nlargest(self.max_categories - 1, chart_spec.y)
            others_value = df[~df.index.isin(df_top.index)][chart_spec.y].sum()
            
            if others_value > 0:
                others_row = pd.DataFrame({
                    chart_spec.x: ["Others"],
                    chart_spec.y: [others_value]
                })
                df = pd.concat([df_top, others_row], ignore_index=True)
            else:
                df = df_top
        
        return [
            {
                "name": str(row[chart_spec.x]),
                "value": float(row[chart_spec.y]) if pd.notna(row[chart_spec.y]) else 0
            }
            for _, row in df.iterrows()
        ]
    
    def _format_standard_chart_data(
        self, 
        chart_spec: ChartSpec, 
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Format data for bar, line, and scatter charts with multi-series support."""
        data = []
        
        for _, row in df.iterrows():
            point = {}
            
            # Add x-axis data
            if chart_spec.x and chart_spec.x in row:
                point[chart_spec.x] = self._format_value_for_json(row[chart_spec.x])
            
            # Add y-axis data  
            if chart_spec.y and chart_spec.y in row:
                point[chart_spec.y] = self._format_value_for_json(row[chart_spec.y])
            
            # Add group_by columns for series grouping
            if chart_spec.group_by:
                for group_col in chart_spec.group_by:
                    if group_col in row:
                        point[group_col] = self._format_value_for_json(row[group_col])
            
            data.append(point)
        
        return data
    
    def _format_value_for_json(self, value: Any) -> Any:
        """Format value for JSON serialization."""
        if pd.isna(value):
            return None
        elif isinstance(value, (np.integer, np.int64)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64)):
            return float(value)
        elif isinstance(value, pd.Timestamp):
            return value.isoformat()
        elif hasattr(value, 'item'):  # numpy scalar
            return value.item()
        else:
            return str(value)
    
    def _calculate_summary_stats(
        self, 
        df: pd.DataFrame, 
        chart_spec: ChartSpec
    ) -> Dict[str, Any]:
        """Calculate comprehensive summary statistics for the chart data."""
        stats = {
            "total_records": len(df),
            "chart_type": chart_spec.chart_type
        }
        
        # Add numeric column statistics
        if chart_spec.y and chart_spec.y in df.columns:
            try:
                y_series = pd.to_numeric(df[chart_spec.y], errors='coerce').dropna()
                if len(y_series) > 0:
                    stats.update({
                        f"{chart_spec.y}_total": float(y_series.sum()),
                        f"{chart_spec.y}_mean": float(y_series.mean()),
                        f"{chart_spec.y}_min": float(y_series.min()),
                        f"{chart_spec.y}_max": float(y_series.max())
                    })
            except Exception:
                pass
        
        # Add categorical statistics
        if chart_spec.x and chart_spec.x in df.columns:
            try:
                unique_values = df[chart_spec.x].nunique()
                stats[f"{chart_spec.x}_unique_count"] = unique_values
            except Exception:
                pass
        
        # Add grouping statistics
        if chart_spec.group_by:
            for group_col in chart_spec.group_by:
                if group_col in df.columns:
                    try:
                        unique_groups = df[group_col].nunique()
                        stats[f"{group_col}_groups"] = unique_groups
                    except Exception:
                        pass
        
        return stats
    
    # Legacy method for backward compatibility
    async def validate_chart_spec(
        self, 
        chart_spec: ChartSpec, 
        csv_metadata: CSVMetadata
    ) -> ChartValidationResult:
        """Legacy validation method - redirects to enhanced validation."""
        # Create a dummy dataframe for validation
        dummy_df = pd.DataFrame(columns=csv_metadata.columns)
        return await self._validate_enhanced_chart_spec(chart_spec, dummy_df, csv_metadata)
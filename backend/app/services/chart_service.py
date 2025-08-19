"""
Chart generation service for converting chart specifications to visualization data.
Similar to a data transformation service in .NET applications.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging

from app.models.chart_models import ChartSpec, ChartData, ChartValidationResult, FilterSpec
from app.models.csv_models import CSVMetadata
from app.core.exceptions import ValidationException, FileProcessingException

logger = logging.getLogger(__name__)


class ChartService:
    """
    Service for generating chart data from specifications and CSV data.
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
        Generate chart data from specification and DataFrame.
        
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
            # Validate chart specification against data
            validation_result = await self.validate_chart_spec(chart_spec, csv_metadata)
            if not validation_result.is_valid:
                raise ValidationException(
                    validation_result.error_message,
                    details={"suggestions": validation_result.suggestions}
                )
            
            # Apply data transformations
            processed_df, transformations = await self._process_dataframe(chart_spec, dataframe)
            
            # Generate chart-specific data
            chart_data = await self._generate_chart_specific_data(chart_spec, processed_df)
            
            # Calculate summary statistics
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
    
    async def validate_chart_spec(
        self, 
        chart_spec: ChartSpec, 
        csv_metadata: CSVMetadata
    ) -> ChartValidationResult:
        """
        Validate chart specification against CSV metadata.
        Similar to validation services in .NET with specific business rules.
        """
        suggestions = []
        
        # Validate required columns exist
        available_columns = set(csv_metadata.columns)
        
        if chart_spec.x and chart_spec.x not in available_columns:
            return ChartValidationResult.failure(
                f"X-axis column '{chart_spec.x}' not found in data",
                suggestions=[f"Available columns: {', '.join(available_columns)}"]
            )
        
        if chart_spec.y and chart_spec.y not in available_columns:
            return ChartValidationResult.failure(
                f"Y-axis column '{chart_spec.y}' not found in data",
                suggestions=[f"Available columns: {', '.join(available_columns)}"]
            )
        
        # Validate group_by columns
        if chart_spec.group_by:
            invalid_groups = [col for col in chart_spec.group_by if col not in available_columns]
            if invalid_groups:
                return ChartValidationResult.failure(
                    f"Group by columns not found: {invalid_groups}",
                    suggestions=[f"Available columns: {', '.join(available_columns)}"]
                )
        
        # Validate chart type requirements
        validation_result = self._validate_chart_type_requirements(chart_spec, csv_metadata)
        if not validation_result.is_valid:
            return validation_result
        
        # Validate filters
        if chart_spec.filters:
            for filter_spec in chart_spec.filters:
                if filter_spec.column not in available_columns:
                    return ChartValidationResult.failure(
                        f"Filter column '{filter_spec.column}' not found in data",
                        suggestions=[f"Available columns: {', '.join(available_columns)}"]
                    )
        
        return ChartValidationResult.success()
    
    def _validate_chart_type_requirements(
        self, 
        chart_spec: ChartSpec, 
        csv_metadata: CSVMetadata
    ) -> ChartValidationResult:
        """Validate chart type specific requirements."""
        chart_type = chart_spec.chart_type
        numeric_cols = set(csv_metadata.get_numeric_columns())
        categorical_cols = set(csv_metadata.get_categorical_columns())
        
        if chart_type == "scatter":
            # Scatter plots need numeric x and y
            if chart_spec.x and chart_spec.x not in numeric_cols:
                return ChartValidationResult.failure(
                    f"Scatter plot X-axis '{chart_spec.x}' must be numeric",
                    suggestions=[f"Numeric columns: {', '.join(numeric_cols)}"]
                )
            if chart_spec.y and chart_spec.y not in numeric_cols:
                return ChartValidationResult.failure(
                    f"Scatter plot Y-axis '{chart_spec.y}' must be numeric",
                    suggestions=[f"Numeric columns: {', '.join(numeric_cols)}"]
                )
        
        elif chart_type == "pie":
            # Pie charts need categorical x and numeric y
            if chart_spec.x and chart_spec.x not in categorical_cols:
                return ChartValidationResult.failure(
                    f"Pie chart categories '{chart_spec.x}' should be categorical",
                    suggestions=[f"Categorical columns: {', '.join(categorical_cols)}"]
                )
            if chart_spec.y and chart_spec.y not in numeric_cols:
                return ChartValidationResult.failure(
                    f"Pie chart values '{chart_spec.y}' must be numeric",
                    suggestions=[f"Numeric columns: {', '.join(numeric_cols)}"]
                )
        
        elif chart_type in ["bar", "line"]:
            # Bar and line charts typically need numeric y
            if chart_spec.y and chart_spec.y not in numeric_cols and chart_spec.aggregation == "none":
                return ChartValidationResult.failure(
                    f"{chart_type.title()} chart Y-axis '{chart_spec.y}' should be numeric or use aggregation",
                    suggestions=["Try using aggregation like 'count', 'sum', or 'mean'"]
                )
        
        return ChartValidationResult.success()
    
    async def _process_dataframe(
        self, 
        chart_spec: ChartSpec, 
        df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Process DataFrame according to chart specification.
        Returns processed DataFrame and list of transformations applied.
        """
        processed_df = df.copy()
        transformations = []
        
        # Apply filters
        if chart_spec.filters:
            processed_df, filter_transformations = self._apply_filters(processed_df, chart_spec.filters)
            transformations.extend(filter_transformations)
        
        # Apply grouping and aggregation
        if chart_spec.group_by or chart_spec.aggregation != "none":
            processed_df, agg_transformations = self._apply_aggregation(
                processed_df, chart_spec
            )
            transformations.extend(agg_transformations)
        
        # Limit data points for performance
        if len(processed_df) > self.max_data_points:
            processed_df = processed_df.head(self.max_data_points)
            transformations.append(f"Limited to {self.max_data_points} data points for performance")
        
        # Sort data for better visualization
        if chart_spec.x and chart_spec.x in processed_df.columns:
            processed_df = processed_df.sort_values(chart_spec.x)
            transformations.append(f"Sorted by {chart_spec.x}")
        
        return processed_df, transformations
    
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
    
    def _apply_aggregation(
        self, 
        df: pd.DataFrame, 
        chart_spec: ChartSpec
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Apply grouping and aggregation to DataFrame."""
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
                if not chart_spec.y:
                    chart_spec.y = 'count'  # Update spec for count
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
                
                agg_df = df.groupby(group_cols)[chart_spec.y].agg(agg_func).reset_index()
                transformations.append(f"Grouped by {group_cols} and applied {agg_func} to {chart_spec.y}")
            
            return agg_df, transformations
            
        except Exception as e:
            logger.warning(f"Aggregation failed: {str(e)}")
            return df, transformations
    
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
        """Format data for bar, line, and scatter charts."""
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
        else:
            return str(value)
    
    def _calculate_summary_stats(
        self, 
        df: pd.DataFrame, 
        chart_spec: ChartSpec
    ) -> Dict[str, Any]:
        """Calculate summary statistics for the chart data."""
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
            unique_values = df[chart_spec.x].nunique()
            stats[f"{chart_spec.x}_unique_count"] = unique_values
        
        return stats